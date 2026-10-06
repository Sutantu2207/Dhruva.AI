# DHRUVA.AI — AI Production Operations & Guardrails Guide

## 1. Core Architectural Invariant

> **AI is NEVER Authoritative Over Academic Truth.**
> Gemini functions solely as an assistive tutor, contextual explainer, and retrieval copilot.
> Absolute authority over grades, prerequisite mastery, retention scores, placement readiness, and remediation sequencing remains in the deterministic engines.

---

## 2. Gemini Integration Configuration

Production configuration variables in `backend/.env.production`:
- `GEMINI_API_KEY`: Enterprise API key for Google Gemini.
- `GEMINI_MODEL`: Default `gemini-1.5-pro` or `gemini-1.5-flash`.
- `AI_MAX_OUTPUT_TOKENS`: Hard cap per inference call (default: 2048).
- `AI_TEMPERATURE`: 0.2 for strict academic assistance, 0.5 for brainstorming.
- `AI_REQUEST_TIMEOUT`: 30 seconds before timing out.

---

## 3. Cost Control & Quotas

- **Per-User Limits**: Max 100 requests per student per day.
- **Per-Institution Limits**: Max 50,000 requests per tenant per day.
- **Token Accounting**: Every AI interaction logs prompt tokens, completion tokens, latency, and estimated cost to the database audit trail.
- **Admin Visibility**: `GET /api/v1/admin/operations/ai` exposes system-wide token velocity and usage breakdowns without exposing student conversation content.

---

## 4. Failure Degradation

If the Gemini API encounters rate limits (HTTP 429) or service outages (HTTP 503):
- The platform **NEVER** synthesizes a fake AI response.
- The platform returns a structured error:
  ```json
  {
    "error": {
      "code": "AI_SERVICE_UNAVAILABLE",
      "message": "AI tutoring services are temporarily degraded. Deterministic assessments and learning modules remain active."
    }
  }
  ```
