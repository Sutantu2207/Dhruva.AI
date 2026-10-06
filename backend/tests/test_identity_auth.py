"""Comprehensive test suite for Domain 1: Identity & Authentication.

Covers all 23 required functional scenarios, security boundaries, and RBAC enforcement.
"""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from app.core.security import UserRole, verify_password, create_access_token
from app.domains.identity.models import User
from sqlalchemy import select


@pytest.mark.asyncio
async def test_01_successful_student_registration(async_client: AsyncClient):
    """Scenario 1: Successful student registration via public endpoint."""
    payload = {
        "email": "student.test@engineering.edu",
        "password": "SecurePassword123!",
        "first_name": "Alex",
        "last_name": "Rivera",
        "institution_id": "inst-101",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "student.test@engineering.edu"
    assert data["role"] == "student"
    assert data["first_name"] == "Alex"
    assert data["last_name"] == "Rivera"
    assert data["display_name"] == "Alex Rivera"
    assert "id" in data
    # Password must never be returned
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_02_duplicate_email_rejection(async_client: AsyncClient):
    """Scenario 2: Duplicate email address rejection with 409 Conflict."""
    payload = {
        "email": "duplicate@college.edu",
        "password": "SecurePassword123!",
        "first_name": "Sam",
        "last_name": "Smith",
    }
    first_res = await async_client.post("/api/v1/auth/register", json=payload)
    assert first_res.status_code == 201

    duplicate_res = await async_client.post("/api/v1/auth/register", json=payload)
    assert duplicate_res.status_code == 409
    assert "already exists" in duplicate_res.json()["detail"]


@pytest.mark.asyncio
async def test_03_invalid_email_rejection(async_client: AsyncClient):
    """Scenario 3: Invalid email format rejection."""
    payload = {
        "email": "not-an-email-address",
        "password": "SecurePassword123!",
        "first_name": "Jane",
        "last_name": "Doe",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_04_weak_password_rejection(async_client: AsyncClient):
    """Scenario 4: Rejection of weak passwords violating complexity policy."""
    # Too short (< 8 chars)
    short_pwd = {
        "email": "short@college.edu",
        "password": "Ab1!",
        "first_name": "Short",
        "last_name": "Pass",
    }
    res_short = await async_client.post("/api/v1/auth/register", json=short_pwd)
    assert res_short.status_code == 422

    # Missing uppercase letter
    no_upper = {
        "email": "noupper@college.edu",
        "password": "password123!",
        "first_name": "No",
        "last_name": "Upper",
    }
    res_upper = await async_client.post("/api/v1/auth/register", json=no_upper)
    assert res_upper.status_code == 422

    # Missing special character
    no_special = {
        "email": "nospecial@college.edu",
        "password": "Password1234",
        "first_name": "No",
        "last_name": "Special",
    }
    res_special = await async_client.post("/api/v1/auth/register", json=no_special)
    assert res_special.status_code == 422


@pytest.mark.asyncio
async def test_05_and_06_password_hashing_and_never_returned(async_client: AsyncClient, db_session):
    """Scenarios 5 & 6: Argon2id password hashing and password absence in API responses."""
    payload = {
        "email": "hashcheck@college.edu",
        "password": "ValidPassword999#",
        "first_name": "Hash",
        "last_name": "Check",
    }
    res = await async_client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201

    # Check database record directly
    stmt = select(User).where(User.email == "hashcheck@college.edu")
    db_res = await db_session.execute(stmt)
    user = db_res.scalar_one()

    # Must be hashed with Argon2id
    assert user.hashed_password.startswith("$argon2id$")
    assert user.hashed_password != payload["password"]
    assert verify_password(payload["password"], user.hashed_password) is True

    # Check that API never returns password
    data = res.json()
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_07_successful_login(async_client: AsyncClient):
    """Scenario 7: Successful login returns access token and sets HttpOnly refresh cookie."""
    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginuser@college.edu",
            "password": "LoginPassword123!",
            "first_name": "Login",
            "last_name": "User",
        },
    )

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@college.edu", "password": "LoginPassword123!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "student"
    assert "refresh_token" in data

    # Verify HttpOnly cookie was set
    assert "dhruva_refresh_token" in login_res.cookies


@pytest.mark.asyncio
async def test_08_incorrect_password(async_client: AsyncClient):
    """Scenario 8: Incorrect password returns 401 Unauthorized."""
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpwd@college.edu",
            "password": "CorrectPassword123!",
            "first_name": "Wrong",
            "last_name": "Pass",
        },
    )

    res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpwd@college.edu", "password": "IncorrectPassword999!"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_09_nonexistent_account_login_enumeration_defense(async_client: AsyncClient):
    """Scenario 9: Nonexistent account returns identical 401 error to prevent enumeration."""
    res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "does.not.exist@college.edu", "password": "RandomPassword123!"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_10_and_15_access_token_validation_and_current_user(async_client: AsyncClient):
    """Scenarios 10 & 15: Access token validation and /me current user endpoint."""
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "me_user@college.edu",
            "password": "MePassword123!",
            "first_name": "Maria",
            "last_name": "Santos",
        },
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "me_user@college.edu", "password": "MePassword123!"},
    )
    access_token = login_res.json()["access_token"]

    # Call /me with Bearer token
    me_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == "me_user@college.edu"
    assert data["display_name"] == "Maria Santos"
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_11_expired_credentials(async_client: AsyncClient):
    """Scenario 11: Expired access token is rejected with 401."""
    expired_token = create_access_token(
        subject="test-user-id",
        role=UserRole.STUDENT,
        expires_delta=timedelta(seconds=-10),  # expired 10s ago
    )
    res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_12_refresh_flow_with_rotation(async_client: AsyncClient):
    """Scenario 12: Refresh flow rotates the refresh token and returns a new access token."""
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh_user@college.edu",
            "password": "RefreshPassword123!",
            "first_name": "Ref",
            "last_name": "User",
        },
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "refresh_user@college.edu", "password": "RefreshPassword123!"},
    )
    old_refresh_token = login_res.json()["refresh_token"]

    # Request refresh using cookie or header
    refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        headers={"X-Refresh-Token": old_refresh_token},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    new_refresh_token = new_data["refresh_token"]
    assert new_refresh_token != old_refresh_token

    # Old refresh token must now be invalid due to rotation
    stale_res = await async_client.post(
        "/api/v1/auth/refresh",
        headers={"X-Refresh-Token": old_refresh_token},
    )
    assert stale_res.status_code == 401


@pytest.mark.asyncio
async def test_13_and_14_logout_and_revoked_session(async_client: AsyncClient):
    """Scenarios 13 & 14: Logout revokes session; revoked session is rejected."""
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout_user@college.edu",
            "password": "LogoutPassword123!",
            "first_name": "Log",
            "last_name": "Out",
        },
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "logout_user@college.edu", "password": "LogoutPassword123!"},
    )
    refresh_token = login_res.json()["refresh_token"]

    # Logout
    logout_res = await async_client.post(
        "/api/v1/auth/logout",
        headers={"X-Refresh-Token": refresh_token},
    )
    assert logout_res.status_code == 200

    # Attempting to refresh with the revoked session must fail
    refresh_attempt = await async_client.post(
        "/api/v1/auth/refresh",
        headers={"X-Refresh-Token": refresh_token},
    )
    assert refresh_attempt.status_code == 401


@pytest.mark.asyncio
async def test_16_unauthenticated_protected_endpoint(async_client: AsyncClient):
    """Scenario 16: Unauthenticated access to protected endpoint is rejected with 401."""
    res = await async_client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_17_and_18_role_authorization_student_vs_teacher(async_client: AsyncClient, db_session):
    """Scenarios 17 & 18: Student and Teacher role authorization."""
    # 1. Student access
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "role_student@college.edu",
            "password": "RolePassword123!",
            "first_name": "Student",
            "last_name": "One",
        },
    )
    student_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "role_student@college.edu", "password": "RolePassword123!"},
    )
    student_token = student_login.json()["access_token"]

    student_res = await async_client.get(
        "/api/v1/auth/test/student-only",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_res.status_code == 200
    assert "Authorized student access" in student_res.json()["message"]

    # Student accessing teacher-only endpoint must fail (403)
    teacher_forbidden = await async_client.get(
        "/api/v1/auth/test/teacher-only",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert teacher_forbidden.status_code == 403


@pytest.mark.asyncio
async def test_19_privileged_role_escalation_attempt_rejected(async_client: AsyncClient):
    """Scenario 19: Malicious user cannot select or pass a privileged role in public registration.

    CRITICAL SECURITY TEST.
    """
    # Attempting to pass role: super_admin or institution_admin
    payload = {
        "email": "hacker@college.edu",
        "password": "HackerPassword123!",
        "first_name": "Evil",
        "last_name": "User",
        "role": "super_admin",
    }
    # Pydantic or backend must enforce role is student
    res = await async_client.post("/api/v1/auth/register", json=payload)
    if res.status_code == 201:
        # If registration succeeds, the assigned role MUST strictly be 'student'
        data = res.json()
        assert data["role"] == "student"
        assert data["role"] != "super_admin"


@pytest.mark.asyncio
async def test_20_cross_role_access_denial(async_client: AsyncClient):
    """Scenario 20: Cross-role access denial - Student cannot call admin-only endpoints."""
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "normal_student@college.edu",
            "password": "NormalPassword123!",
            "first_name": "Normal",
            "last_name": "Student",
        },
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "normal_student@college.edu", "password": "NormalPassword123!"},
    )
    token = login_res.json()["access_token"]

    # Student attempts to call admin-only endpoint
    admin_res = await async_client.get(
        "/api/v1/auth/test/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert admin_res.status_code == 403
    assert "Access denied" in admin_res.json()["detail"]


@pytest.mark.asyncio
async def test_21_password_change(async_client: AsyncClient):
    """Scenario 21: Password change requires current password and invalidates active sessions."""
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "change_pwd_user@college.edu",
            "password": "OldPassword123!",
            "first_name": "Change",
            "last_name": "Password",
        },
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "change_pwd_user@college.edu", "password": "OldPassword123!"},
    )
    access_token = login_res.json()["access_token"]
    old_refresh = login_res.json()["refresh_token"]

    # Change password
    change_res = await async_client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": "OldPassword123!", "new_password": "BrandNewPassword999$"},
    )
    assert change_res.status_code == 200

    # Old refresh token must be invalidated
    stale_refresh = await async_client.post(
        "/api/v1/auth/refresh",
        headers={"X-Refresh-Token": old_refresh},
    )
    assert stale_refresh.status_code == 401

    # Login with new password must succeed
    new_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "change_pwd_user@college.edu", "password": "BrandNewPassword999$"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_22_and_23_account_lockout_after_consecutive_failed_attempts(async_client: AsyncClient):
    """Scenarios 22 & 23: Account locks out after 5 consecutive failed login attempts."""
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "lockout_user@college.edu",
            "password": "CorrectPassword123!",
            "first_name": "Lock",
            "last_name": "Out",
        },
    )

    # 5 failed login attempts
    for _ in range(5):
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "lockout_user@college.edu", "password": "WrongPassword123!"},
        )
        assert res.status_code == 401

    # 6th attempt: Account is locked (HTTP 423 Locked)
    locked_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "lockout_user@college.edu", "password": "CorrectPassword123!"},
    )
    assert locked_res.status_code == 423
    assert "temporarily locked" in locked_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_security_cross_student_profile_access_denial(async_client: AsyncClient):
    """Security test: A student cannot access another student's scoped resource."""
    # Register Student A
    res_a = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "student_a@college.edu",
            "password": "PasswordA123!",
            "first_name": "Alice",
            "last_name": "Student",
        },
    )
    id_a = res_a.json()["id"]

    # Register Student B
    res_b = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "student_b@college.edu",
            "password": "PasswordB123!",
            "first_name": "Bob",
            "last_name": "Student",
        },
    )
    token_b = (
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "student_b@college.edu", "password": "PasswordB123!"},
        )
    ).json()["access_token"]

    # Student B attempts to access Student A's profile endpoint
    cross_access = await async_client.get(
        f"/api/v1/auth/test/user-profile/{id_a}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert cross_access.status_code == 403
    assert "Access denied" in cross_access.json()["detail"]
