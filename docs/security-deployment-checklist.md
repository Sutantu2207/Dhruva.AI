# DHRUVA.AI — PRODUCTION SECURITY DEPLOYMENT CHECKLIST
**Mandatory Hardening, Verification Commands & Zero-Trust Audit Procedures**

---

## 1. Secrets & Cryptographic Hygiene

### Item SEC-01: Strong Unpredictable SECRET_KEY
- **WHAT**: Validate that `SECRET_KEY` is a 64-character high-entropy hex string and does not contain default fallback strings.
- **WHERE**: `.env` file and `backend/app/core/config.py`.
- **WHY**: JWT tokens and session signatures depend on HMAC-SHA256 integrity; a weak key allows token forgery.
- **CONFIGURATION**: `SECRET_KEY=$(openssl rand -hex 32)`
- **COMMAND**:
  ```bash
  python -c "from app.core.config import settings; settings.validate_production_secrets(); print('SECRET_KEY VALID')"
  ```
- **EXPECTED RESULT**: Prints `SECRET_KEY VALID`.
- **FAILURE MODE**: Raises `ValueError: CRITICAL PRODUCTION VIOLATION: SECRET_KEY must be an unpredictable secret...`
- **ROLLBACK**: Generate and set a new 32+ char key using `openssl rand -hex 32`.

---

### Item SEC-02: Secure HTTPS Cookies
- **WHAT**: Enforce `COOKIE_SECURE=true` and `COOKIE_SAMESITE=lax` in production.
- **WHERE**: `backend/app/core/config.py`.
- **WHY**: Prevents credential leakage across unencrypted plain HTTP connections.
- **CONFIGURATION**: `COOKIE_SECURE=true`, `COOKIE_SAMESITE=lax`
- **COMMAND**:
  ```bash
  grep "COOKIE_SECURE" .env
  ```
- **EXPECTED RESULT**: `COOKIE_SECURE=true`
- **FAILURE MODE**: Browser rejects cookie transmission over insecure channels or allows interception.
- **ROLLBACK**: Revert `.env` and restart backend.

---

## 2. Ingress & Network Hardening

### Item SEC-03: Zero Database/Redis Port Exposure
- **WHAT**: PostgreSQL (5432) and Redis (6379) must **NOT** bind to host public interfaces.
- **WHERE**: `docker-compose.production.yml`.
- **WHY**: Direct port exposure invites brute force, credential stuffing, and ransomware.
- **CONFIGURATION**: Internal network `dhruva_internal` only; no `ports:` mapping under postgres or redis services.
- **COMMAND**:
  ```bash
  docker compose -f docker-compose.production.yml ps
  netstat -tuln | grep -E "5432|6379"
  ```
- **EXPECTED RESULT**: No listener on external 0.0.0.0:5432 or 0.0.0.0:6379.
- **FAILURE MODE**: Port scanning reveals open database ports to the internet.
- **ROLLBACK**: Remove `ports:` stanza from data services in compose file.

---

### Item SEC-04: Production HTTP Security Headers
- **WHAT**: Validate presence of HSTS, CSP, X-Content-Type-Options, X-Frame-Options, and Referrer-Policy headers.
- **WHERE**: Reverse proxy Nginx (`deploy/nginx/conf.d/dhruva.conf`) & ASGI middleware (`backend/app/main.py`).
- **WHY**: Mitigates clickjacking, MIME sniffing, and cross-site scripting (XSS).
- **COMMAND**:
  ```bash
  curl -I https://app.dhruva.edu.in/
  ```
- **EXPECTED RESULT**:
  ```http
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy: default-src 'self'; ...
  ```
- **FAILURE MODE**: Headers absent, triggering security scanner warnings.
- **ROLLBACK**: Re-apply headers block in Nginx virtual host.

---

### Item SEC-05: Strict CORS Origins with Credentials
- **WHAT**: Disallow wildcard (`*`) origins in `CORS_ORIGINS`.
- **WHERE**: `.env` and `app/core/config.py`.
- **WHY**: Wildcard origins paired with credentials allow arbitrary malicious domains to read student records.
- **COMMAND**:
  ```bash
  python -c "from app.core.config import settings; assert '*' not in settings.CORS_ORIGINS; print('CORS STRICT')"
  ```
- **EXPECTED RESULT**: Prints `CORS STRICT`.
- **FAILURE MODE**: Browser allows cross-origin credential sharing to untrusted origins.
- **ROLLBACK**: Specify explicit FQDNs in `CORS_ORIGINS`.

---

## 3. Container & Runtime Isolation

### Item SEC-06: Non-Root Container Execution
- **WHAT**: Containers must run under unprivileged system users (`dhruva:dhruva` and `nextjs:nodejs`).
- **WHERE**: `Dockerfile.backend` (UID 10001) & `Dockerfile.frontend` (UID 10001).
- **WHY**: Defense-in-depth: container breakout does not grant host root privileges.
- **COMMAND**:
  ```bash
  docker compose -f docker-compose.production.yml exec backend id
  docker compose -f docker-compose.production.yml exec frontend id
  ```
- **EXPECTED RESULT**: `uid=10001(dhruva) gid=10001(dhruva)` and `uid=10001(nextjs) gid=10001(nodejs)`.
- **FAILURE MODE**: `uid=0(root)` running process.
- **ROLLBACK**: Rebuild with `USER <unprivileged>` directives.

---

### Item SEC-07: Coding Sandbox Execution Isolation
- **WHAT**: Arbitrary untrusted student code is **NEVER** executed in the main backend process.
- **WHERE**: `backend/app/domains/assessment/evaluators/coding.py`.
- **WHY**: Prevents remote code execution (RCE), host compromise, and data exfiltration.
- **COMMAND**:
  ```bash
  python -c "from app.domains.assessment.evaluators.coding import get_code_execution_provider; p = get_code_execution_provider(); print(type(p).__name__)"
  ```
- **EXPECTED RESULT**: `HttpSandboxProvider` or `UnavailableCodeExecutionProvider`. Never executes locally.
- **FAILURE MODE**: Untrusted code runs in Uvicorn worker.
- **ROLLBACK**: Set `_active_provider = UnavailableCodeExecutionProvider()`.
