# DHRUVA.AI — Security Architecture & Hardening Guide

## 1. Authentication & Session Security

- **JWT Tokens**:
  - Access tokens signed via HS256 / RS256 with strict expiration (15-60 minutes).
  - Refresh tokens stored in HttpOnly, Secure, SameSite=Lax cookies to defend against XSS token harvesting.
  - No access tokens or user credentials stored in `localStorage` or `sessionStorage`.
- **Password Policies**:
  - Passwords hashed using `bcrypt` (or Argon2id) with work factor >= 12.
  - Password reset tokens cryptographically generated with 15-minute expiration windows.
- **Fail-Fast Startup**:
  - In production (`APPLICATION_ENV=production`), application startup halts immediately if `SECRET_KEY` is missing or below 32 characters in length.

---

## 2. Authorization & Multi-Tenant Isolation

- **Role-Based Access Control (RBAC)**:
  - Strict role hierarchy: `SUPER_ADMIN`, `INSTITUTION_ADMIN`, `HOD`, `FACULTY`, `STUDENT`.
  - Endpoint decorators enforce role authorization on every sensitive API path.
- **Institution Multi-Tenant Isolation**:
  - Every resource query filters by `institution_id` matching the authenticated JWT context.
  - Prevents cross-institution data leakage (Institution A cannot query Institution B resources).
- **Inverted Denial of Insecure Direct Object References (IDOR)**:
  - Students cannot inspect another student's unverified projects, remediation assignments, or AI tutor chats.
  - Faculty cannot grade courses outside their assigned department without explicit institution-level clearance.

---

## 3. Web Security Headers & Sanitization

The application injects security headers across all responses:
- `X-Content-Type-Options: nosniff` (prevents MIME sniffing)
- `X-Frame-Options: DENY` (clickjacking defense)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` (Production HTTPS enforcement)
- File Upload Traversal Guard: Slashes and relative segments (`..`) stripped from storage keys.
