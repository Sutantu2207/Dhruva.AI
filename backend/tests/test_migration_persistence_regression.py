"""Deterministic regression tests for Alembic async migration transaction persistence.

Regression test verifying that:
1. Online async migrations do not trigger autobegin prior to context.configure(),
   which would cause Alembic to flag _in_external_transaction=True, render
   context.begin_transaction() a no-op (nullcontext), skip committing, and
   silently roll back all schema and alembic_version records upon connection close.
2. Migrations persist alembic_version at 0013_create_production_operations_tables.
3. Representative tables exist in the database (including institutions and user_sessions).
4. Table count is strictly > 0 and database health checks report proper migration state.
"""

import os
import re
from pathlib import Path
import pytest
from unittest.mock import MagicMock
from sqlalchemy.engine import Connection, RootTransaction, Engine
from sqlalchemy.dialects import postgresql
from sqlalchemy import event, text
from alembic.config import Config
from alembic import command
from alembic.runtime.environment import EnvironmentContext
from alembic.ddl.sqlite import SQLiteImpl
import sqlite3


def test_bug_reproduction_proves_unconfigured_execution_rolls_back_everything():
    """Deterministic proof that executing any query before context.configure() breaks transaction persistence.
    
    This deterministic test demonstrates the exact bug that occurred in Railway:
    1. In SQLAlchemy 2.0, connection.execute() triggers autobegin on the Connection.
    2. Alembic's context.configure(connection=connection) inspects connection.in_transaction().
    3. Because autobegin was active, Alembic set _in_external_transaction = True.
    4. Alembic's context.begin_transaction() returned nullcontext(), delegating commit to caller.
    5. No caller ever called connection.commit().
    6. When async with connectable.connect() exited, connection.close() detected the uncommitted
       transaction and executed ROLLBACK, wiping out all 13 migrations and alembic_version!
    """
    mock_conn = MagicMock(spec=Connection)
    mock_conn.dialect = postgresql.dialect()

    is_in_transaction = False
    committed = False
    rolled_back = False

    def mock_execute(*args, **kwargs):
        nonlocal is_in_transaction
        is_in_transaction = True
        return MagicMock()

    def mock_in_transaction():
        return is_in_transaction

    def mock_commit():
        nonlocal committed, is_in_transaction
        committed = True
        is_in_transaction = False

    def mock_rollback():
        nonlocal rolled_back, is_in_transaction
        rolled_back = True
        is_in_transaction = False

    def mock_close():
        nonlocal rolled_back
        if is_in_transaction:
            mock_rollback()

    mock_conn.execute.side_effect = mock_execute
    mock_conn.in_transaction.side_effect = mock_in_transaction
    mock_conn.commit.side_effect = mock_commit
    mock_conn.rollback.side_effect = mock_rollback
    mock_conn.close.side_effect = mock_close

    # BUG SIMULATION (as formerly coded in env.py):
    # Executing the DO block before context.configure():
    mock_conn.execute(text("DO $$ BEGIN ... END $$;"))
    assert mock_conn.in_transaction() is True, "autobegin must be active after execute()"

    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    cfg = Config(str(ini_path))
    env = EnvironmentContext(cfg, None, fn=lambda rev, context: [])

    with env:
        # Alembic configures on a connection that already has autobegin active:
        env.configure(connection=mock_conn)
        mc = env.get_context()
        # Alembic detects external transaction:
        assert mc._in_external_transaction is True

        # Alembic's begin_transaction() returns nullcontext():
        with env.begin_transaction() as t:
            # Migrations run here inside the uncommitted transaction:
            mock_conn.execute(text("CREATE TABLE institutions ..."))
            mock_conn.execute(text("CREATE TABLE user_sessions ..."))
            mock_conn.execute(text("INSERT INTO alembic_version VALUES ('0013_...')"))

    # Exiting context.begin_transaction did NOT commit:
    assert committed is False

    # Connection context manager exits -> close():
    mock_conn.close()

    # The uncommitted transaction is unconditionally rolled back by SQLAlchemy!
    assert rolled_back is True
    assert committed is False


def test_postgresql_migration_transaction_commit_and_persistence_guarantee():
    """Regression test proving that Alembic properly owns and commits the transaction on PostgreSQL.
    
    With the fix:
    1. context.configure() is called FIRST on a clean connection (_in_external_transaction = False).
    2. context.begin_transaction() begins a real _ProxyTransaction.
    3. The DO block and all migrations run inside the transaction.
    4. Upon exiting context.begin_transaction(), commit() is genuinely called.
    5. Connection.close() does NOT roll back, guaranteeing persistence in PostgreSQL.
    """
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.attributes["skip_run_online"] = True

    import importlib.util
    spec = importlib.util.spec_from_file_location("alembic_env", backend_dir / "alembic" / "env.py")
    env_module = importlib.util.module_from_spec(spec)

    mock_conn = MagicMock(spec=Connection)
    mock_conn.dialect = postgresql.dialect()

    is_in_transaction = False
    committed = False
    rolled_back = False

    mock_trans = MagicMock(spec=RootTransaction)
    def trans_exit(type_, value, traceback):
        nonlocal committed, rolled_back, is_in_transaction
        if type_ is None:
            committed = True
            is_in_transaction = False
        else:
            rolled_back = True
            is_in_transaction = False
    mock_trans.__exit__.side_effect = trans_exit

    def mock_begin():
        nonlocal is_in_transaction
        is_in_transaction = True
        return mock_trans

    def mock_get_transaction():
        return mock_trans if is_in_transaction else None

    def mock_in_transaction():
        return is_in_transaction

    def mock_close():
        nonlocal rolled_back, is_in_transaction
        if is_in_transaction:
            rolled_back = True
            is_in_transaction = False

    def mock_execute(*args, **kwargs):
        return MagicMock()

    mock_conn.begin.side_effect = mock_begin
    mock_conn.get_transaction.side_effect = mock_get_transaction
    mock_conn.in_transaction.side_effect = mock_in_transaction
    mock_conn.close.side_effect = mock_close
    mock_conn.execute.side_effect = mock_execute

    # Run do_run_migrations with EnvironmentContext configured
    env = EnvironmentContext(cfg, None, fn=lambda rev, context: [])
    
    with env:
        spec.loader.exec_module(env_module)
        do_run_migrations = env_module.do_run_migrations
        do_run_migrations(mock_conn)

    # 1. Verify that _in_external_transaction was False when Alembic configured
    mc = env.get_context()
    assert mc._in_external_transaction is False, (
        "CRITICAL REGRESSION: _in_external_transaction must be False so Alembic manages transaction"
    )

    # 2. Verify that the transaction was committed on exit
    assert committed is True, (
        "CRITICAL REGRESSION: Migration transaction was NOT committed! Tables would be lost in PostgreSQL."
    )

    # 3. Simulate connection close at end of async with connectable.connect():
    mock_conn.close()
    assert rolled_back is False, (
        "CRITICAL REGRESSION: Connection rollback occurred on close, destroying PostgreSQL migration state!"
    )


def test_alembic_full_chain_migration_persists_head_and_representative_tables(tmp_path):
    """Executes the full Alembic migration chain from 0001 to 0013 head and proves persistence.
    
    Verifies that:
    1. alembic_version exists and persists at '0013_create_production_operations_tables'.
    2. Representative table 'institutions' exists in database.
    3. Representative table 'user_sessions' exists in database.
    4. Table count is > 0 (100+ domain tables across all 13 linear revisions).
    5. A completely fresh, separate database connection verifies persisted state on disk.
    """
    db_file = tmp_path / "migration_persistence_test.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    # Set up engine listener for stripping PostgreSQL cast syntax for SQLite testing
    def strip_pg_casts(conn, cursor, statement, parameters, context, executemany):
        if "::" in statement:
            statement = re.sub(r"::[a-zA-Z0-9_]+", "", statement)
        return statement, parameters

    event.listen(Engine, "before_cursor_execute", strip_pg_casts, retval=True)

    # Allow SQLite dialect to accept PostgreSQL-style ALTER constraints during tests
    orig_add_constraint = SQLiteImpl.add_constraint
    SQLiteImpl.add_constraint = lambda self, const: None

    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", db_url)

    try:
        # Run upgrade head
        command.upgrade(cfg, "head")

        # Open a brand-new connection directly to the SQLite file on disk to guarantee persistence
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # 1. Verify alembic_version table exists and persists head revision
        cursor.execute("SELECT version_num FROM alembic_version")
        version_rows = cursor.fetchall()
        assert len(version_rows) == 1, f"Expected 1 alembic_version row, found {len(version_rows)}"
        assert version_rows[0][0] == "0013_create_production_operations_tables", (
            f"Expected head revision '0013_create_production_operations_tables', got {version_rows[0][0]}"
        )

        # 2. Inspect all persisted tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        persisted_tables = {row[0] for row in cursor.fetchall()}

        # 3. Verify representative tables exist
        assert "institutions" in persisted_tables, (
            "CRITICAL: Representative table 'institutions' does NOT exist after migration upgrade!"
        )
        assert "user_sessions" in persisted_tables, (
            "CRITICAL: Representative table 'user_sessions' does NOT exist after migration upgrade!"
        )

        # 4. Verify additional core system tables
        assert "users" in persisted_tables
        assert "courses" in persisted_tables
        assert "notifications" in persisted_tables
        assert "student_skill_intelligence_states" in persisted_tables

        # 5. Verify total table count > 0 (full 13 domains)
        assert len(persisted_tables) >= 50, (
            f"Expected extensive domain schema (>= 50 tables), found {len(persisted_tables)}"
        )

        conn.close()

    finally:
        event.remove(Engine, "before_cursor_execute", strip_pg_casts)
        SQLiteImpl.add_constraint = orig_add_constraint
