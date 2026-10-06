# DHRUVA.AI — Object Storage Architecture

## 1. Provider Abstraction

DHRUVA.AI implements a pluggable `StorageProvider` abstraction (`app.core.storage`):
- `LocalDiskStorageProvider`: Used in development and air-gapped test environments. Stores files under `backend/storage/` with strict directory traversal prevention.
- `S3ObjectStorageProvider`: Used in production. Interacts with S3-compatible endpoints (AWS S3, Cloudflare R2, MinIO, Wasabi) using TLS.

---

## 2. File Upload Security Constraints

1. **Path Traversal Defenses**:
   Storage keys are sanitized using regex sanitization (`[^a-zA-Z0-9_\-\./]`) and traversal tokens (`..`) are stripped.
2. **Private Storage by Default**:
   All uploaded academic assets (transcripts, project repos, certificates) are stored privately with ACLs restricting direct public access.
3. **Presigned URLs**:
   Asset retrieval generates short-lived presigned URLs (default 15 minutes) available only to authorized users.
4. **MIME & Extension Validation**:
   Only allowed file extensions (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.zip`, `.csv`) are accepted for upload.
