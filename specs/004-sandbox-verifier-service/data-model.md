# Phase 1 Data Model: Spec 004 — sandbox-verifier-service

## 1. Domain Entities & Database Schema

### 1.1 `verification_runs` Table
Tracks ephemeral verification jobs, compiler outputs, and generated manifest/zip artifacts.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUIDv4 string identifier |
| `user_id` | VARCHAR(36) | NOT NULL, INDEX | Colleague initiating the run |
| `client_code` | VARCHAR(64) | NOT NULL, INDEX | Target client account slug |
| `job_id` | VARCHAR(36) | NULLABLE, INDEX | Reference to AI generation job (Port 8003) |
| `status` | VARCHAR(30) | NOT NULL | `INITIALIZED`, `COMPILING`, `SUCCESS`, `COMPILATION_FAILED`, `ERROR` |
| `compilation_output` | TEXT | NULLABLE | Stdout/stderr from Maven or syntax compiler |
| `duration_ms` | INTEGER | NOT NULL, DEFAULT 0 | Verification duration in milliseconds |
| `manifest_json` | TEXT | NULLABLE | JSON string of SHA-256 verification manifest |
| `zip_path` | VARCHAR(500) | NULLABLE | Local file path to the generated `.zip` |
| `created_at` | DATETIME | NOT NULL | UTC creation timestamp |
| `updated_at` | DATETIME | NOT NULL | UTC last update timestamp |

---

## 2. Pydantic Schemas

### 2.1 Verification Requests & Responses
- `RunCreateRequest`:
  - `client_code`: `str`
  - `job_id`: `Optional[str] = None`
  - `files`: `Dict[str, str]` (relative path -> file content)
  - `auto_verify`: `bool = True`
- `FileHash`:
  - `path`: `str`
  - `sha256`: `str`
  - `size_bytes`: `int`
- `VerificationManifest`:
  - `generated_at`: `datetime`
  - `run_id`: `str`
  - `client_code`: `str`
  - `verification_status`: `str`
  - `files`: `List[FileHash]`
- `RunResponse`:
  - `id`: `str`
  - `user_id`: `str`
  - `client_code`: `str`
  - `job_id`: `Optional[str]`
  - `status`: `str`
  - `compilation_output`: `Optional[str]`
  - `duration_ms`: `int`
  - `manifest`: `Optional[VerificationManifest]`
  - `download_url`: `str`
  - `created_at`: `datetime`

