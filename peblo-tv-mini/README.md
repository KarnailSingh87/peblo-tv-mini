# Peblo TV Mini 📺

> **Content CMS → Pre-Flight Validation → Atomic Publication → Netflix-Style Kid Streaming Experience**  
> *Full-Stack Platform Engineering Challenge (FastAPI + React/TypeScript + PostgreSQL)*

---

## 1. Project Overview

**Peblo TV Mini** is a child-friendly streaming platform designed with a clean architectural separation between:
1. **Internal CMS Studio (`:3001`)**: A content operations portal for editors and administrators to manage shows, organize seasons, upload artwork with strict aspect ratio constraints, review validation blockers, and publish immutable streaming catalogue snapshots.
2. **Viewer Experience (`:3000`)**: A high-performance, child-safe streaming web application that reads **strictly** from the pre-published, immutable catalogue snapshot—completely decoupled from the transactional database.

---

## 2. Architecture

```
                                  [Content Editors / Admins]
                                              │
                                              ▼
                                 ┌────────────────────────┐
                                 │   Internal CMS Studio  │ (:3001)
                                 └────────────┬───────────┘
                                              │ (REST + JWT Auth)
                                              ▼
                                 ┌────────────────────────┐
                                 │   FastAPI Backend API  │ (:8000)
                                 └───────┬────────┬───────┘
                                         │        │
                     ┌───────────────────┘        └───────────────────┐
                     │ (Transactional CRUD)                           │ (Atomic Publish)
                     ▼                                                ▼
         ┌────────────────────────┐                      ┌────────────────────────┐
         │ PostgreSQL 16 Database │                      │ Live `catalogue.json`  │
         │ - Shows, Seasons, Eps  │                      │ & Storage (Disk / R2)  │
         │ - Artwork Metadata     │                      └────────────┬───────────┘
         │ - PublishRuns & Users  │                                   │
         └────────────────────────┘                                   │ (Pure Static Reads / Search)
                                                                      ▼
                                                         ┌────────────────────────┐
                                                         │    Viewer Web App      │ (:3000)
                                                         │    (Netflix-Style UI)  │
                                                         └────────────────────────┘
```

---

## 3. Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2 (ORM), Alembic (Migrations), Pillow (Image validation), Pydantic v2, Pytest.
- **Database**: PostgreSQL 16 (production/docker), SQLite (in-memory for instant testing).
- **Internal CMS**: React 18, TypeScript, Vite, TanStack Query v5, Tailwind CSS, Lucide Icons, Wouter.
- **Viewer App**: React 18, TypeScript, Vite, TanStack Query v5, Tailwind CSS, Lucide Icons, Wouter.
- **Storage**: Pluggable storage abstraction (`LocalStorage` for local disk, ready for `Cloudflare R2` / `AWS S3`).
- **Containerization & CI**: Docker Compose, Multi-stage Dockerfiles, Nginx Alpine, GitHub Actions CI.

---

## 4. How to Run Locally (Without Docker)

### Prerequisites
- Python 3.9+ installed
- Node.js 20+ and npm installed

### 1. Backend Setup
```bash
# From workspace root
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Run migrations and seed data
alembic upgrade head
python -m backend.app.db.seed

# Start FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```

### 2. CMS Setup
```bash
cd frontend/cms
npm install
npm run dev
# CMS runs on http://localhost:3001
```

### 3. Viewer Setup
```bash
cd frontend/viewer
npm install
npm run dev
# Viewer runs on http://localhost:3000
```

---

## 5. Docker Compose Instructions

Launch the entire ecosystem with healthchecks, persistent volumes, and auto-seeding:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Build and start all 4 services
docker compose up --build
```

### Local URLs & Ports
- **Viewer Web App**: [`http://localhost:3000`](http://localhost:3000)
- **CMS Content Studio**: [`http://localhost:3001`](http://localhost:3001)
- **FastAPI Backend API**: [`http://localhost:8000`](http://localhost:8000)
- **Interactive Swagger Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **Health Check Endpoint**: [`http://localhost:8000/api/v1/health`](http://localhost:8000/api/v1/health)

---

## 6. Test Instructions

Run the complete 49-test backend test suite covering authentication, RBAC, artwork validation, validation reports, catalogue generation, atomic publishing, and search:

```bash
# Run pytest with coverage
PYTHONPATH=. pytest backend/tests -v
```

---

## 7. Demo Users & Roles

Seeded automatically during database initialization:

| Username | Password | Role | Permissions |
|---|---|---|---|
| `admin` | `admin123` | **Admin** | Full CMS CRUD, Artwork upload, Validation report, **Publish catalogue**, View publish history |
| `editor` | `editor123` | **Editor** | Full CMS CRUD, Artwork upload, Validation report *(Publishing forbidden: returns HTTP 403)* |

---

## 8. API Overview

### Public Viewer APIs (Reads ONLY `catalogue.json`)
- `GET /api/v1/catalog`: Returns the live published catalogue snapshot.
- `GET /api/v1/catalog/search?q=&category=&language=&section=&page=`: Server-side composable search against the published catalogue.
- `GET /health` & `GET /api/v1/health`: Probes database connectivity (`SELECT 1`) and storage subsystem.

### CMS / Admin APIs (Protected by JWT)
- `POST /api/v1/auth/login`: Issues JWT access token.
- `GET /api/v1/auth/me`: Returns current user details and role.
- `GET`, `POST` `/api/v1/shows`: List (paginated/filtered) and create shows.
- `GET`, `PUT`, `DELETE` `/api/v1/shows/{id}`: Show details, update, and cascade delete.
- `GET`, `POST` `/api/v1/shows/{id}/seasons`: Manage show seasons.
- `GET`, `POST` `/api/v1/seasons/{id}/episodes`: Manage season episodes.
- `GET`, `PUT`, `DELETE` `/api/v1/episodes/{id}`: Episode details, update, and delete.
- `POST /api/v1/artwork/upload`: Uploads and validates Poster (2:3), Banner (16:9), or Thumbnail (16:9).
- `GET /api/v1/admin/validation-report`: Pre-flight audit report identifying publication blockers.
- `POST /api/v1/admin/catalog/publish`: Compiles and atomically publishes the live catalogue (Admin only).
- `GET /api/v1/admin/catalog/publish-runs`: Audit history of all previous publish attempts (Admin only).

---

## 9. Written Reasoning & Architectural Decisions

### A. Atomic Publishing Explanation
Directly writing or truncating `catalogue.json` while thousands of concurrent viewers stream content creates race conditions and partial payload corruption.
**Our Atomic Strategy**:
1. **Pre-flight Audit**: Validation checks run; if blocking issues exist, generation halts with zero storage writes.
2. **Deterministic Compilation**: Generates the catalogue JSON in memory.
3. **Staged Versioned File**: Writes to a timestamped file (`catalogue_v{N}.json.tmp`) and flushes to disk (`os.fsync`).
4. **POSIX Atomic Replacement**: Uses `os.replace()` to atomically swap the file pointer to `catalogue.json`.
5. **PublishRun Audit**: Records execution timestamp, version, status, and metrics in PostgreSQL. If the process crashes before step 4, the existing live catalogue remains untouched.

### B. Storage Abstraction
Business logic relies on an abstract `Storage` interface (`upload`, `delete`, `exists`, `get_url`, `get_bytes`).
- **Development**: `LocalStorage` writes to local disk with strict path sanitization preventing directory traversal.
- **Production**: Switching `STORAGE_TYPE=r2` redirects assets to Cloudflare R2 / AWS S3 with signed URLs and CDN caching without altering any endpoint handlers or models.

### C. Why Use a Pre-Published Catalogue?
1. **Zero Database Contention**: High-traffic viewer reads and video discovery do not compete for PostgreSQL connections or CPU with CMS editorial updates.
2. **Sub-Millisecond Edge Latency**: Static snapshots can be pushed to CDN edge caches (Cloudflare KV / Fastly) globally.
3. **Immutable Snapshot Guarantees**: Prevents half-edited draft episodes or broken relationships from appearing to viewers mid-browse.

### D. Search Approach and Scaling Limitations
- **Current Implementation**: Fast server-side linear scanning across the parsed published catalogue structure in memory ($\approx 200\text{ KB}$, $< 2\text{ ms}$).
- **Scaling Limitations**: Linear in-memory search is optimal for $< 1,000$ shows and $< 50,000$ episodes.
- **Evolution Path**: When scaling to $100,000+$ multilingual titles with full subtitle transcripts, search should transition to:
  1. PostgreSQL Full-Text Search (`tsvector` with GIN indexing) on dedicated read replicas, or
  2. A dedicated search engine (Typesense / Meilisearch / Elasticsearch) updated asynchronously via webhook on every successful `PublishRun`.

### E. What Was Intentionally Left Out
- **Full Video Transcoding/Streaming Pipeline**: Focused squarely on CMS workflows, metadata validation, language collapsing, and Netflix-style browsing.
- **Complex OAuth2 Refresh Token Rotation**: Used clean HMAC-SHA256 JWTs with 24-hour expiration to keep review operability straightforward.

### F. AI Tools Usage & Decision Log
- **Where Accepted**: Scaffolding repetitive Pydantic schemas, initial TypeScript type declarations, and Tailwind layout skeletons.
- **Where Corrected/Rejected**:
  - *Client-side search*: AI suggested client-only JavaScript filtering over the raw payload in React; **rejected** in favor of server-side search adhering to platform engineering isolation.
  - *Data Mutability*: AI suggested modifying database records during catalogue generation; **rejected** to guarantee pure, non-mutating compilations.
  - *Bcrypt 72-byte truncation*: Handled compatibility with `passlib` to ensure reliable cross-platform hashing.

---

## 10. Security Considerations

- **Server-Side Enforcement**: Permissions and validation rules are strictly enforced in Python; frontend buttons are disabled for UX only.
- **File Upload Security**:
  - Validates file size ($\le 200\text{ KB}$), image format (JPEG/PNG/WebP), aspect ratios, and dimensions using Pillow server-side.
  - Generated UUID filenames prevent path traversal (`../`) and overwrite exploits.
- **Rate Limiting & CORS**: Restricted to allowed origins.
- **Secrets Management**: No secrets committed to git. Managed via environment variables and cloud secret managers.

---

## 11. Production Deployment & Alerting

### Cloud Deployment Pipeline
1. **Immutable Builds**: Docker images built and tagged with the Git commit SHA.
2. **Registry Push**: Uploaded to private AWS ECR / Google Artifact Registry with CVE scanning.
3. **Secrets Injection**: Secrets pulled at runtime from AWS Secrets Manager / Vault into environment variables.
4. **Pre-Traffic Migrations**: `alembic upgrade head` runs as an ephemeral pre-deployment task.
5. **Rolling Updates**: Zero-downtime rolling replacement with automated rollback if `/api/v1/health` fails.

### The #1 Metric to Alert On: **Repeated Catalogue Publish Failures**
- **Why**: A failed publish means editors believe new content is live while viewers continue seeing outdated catalogues, causing content drift and breaking release schedules.
- **Threshold**: 2 consecutive failed runs (`status == "failed"` in `PublishRun`) triggers a P1 alert to `#content-ops` and on-call engineering.

---

## 12. Environment Variables Summary

Documented fully in [`.env.example`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/.env.example):
- `DATABASE_URL`: SQLAlchemy PostgreSQL connection string.
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT auth configuration.
- `STORAGE_TYPE`, `LOCAL_STORAGE_DIR`: Storage engine (`"local"` / `"r2"` / `"s3"`).
- `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`: Cloud storage credentials.
- `CORS_ORIGINS`, `VITE_API_BASE_URL`: Networking and frontend base URLs.

---

## 13. Approximate Time Spent by Phase

| Phase | Major Area | Time Spent |
|---|---|---|
| **Phase 1** | Seed Data Analysis & PostgreSQL Data Modeling (SQLAlchemy 2 + Alembic) | ~2.0 hours |
| **Phase 2** | Authentication, JWT, RBAC & CRUD APIs for Shows/Seasons/Episodes | ~2.0 hours |
| **Phase 3** | Pillow Artwork Validation & Storage Abstraction (Local/R2) | ~1.5 hours |
| **Phase 4** | Pre-Flight Validation Audit Engine & Atomic Catalogue Publisher | ~1.5 hours |
| **Phase 5** | Viewer APIs & Server-Side Catalogue Search | ~1.0 hours |
| **Phase 6** | Internal CMS Frontend (React + TS + TanStack Query + Tailwind) | ~2.0 hours |
| **Phase 7** | Viewer Web App (React + TS + Multilingual Audio Switcher) | ~1.5 hours |
| **Phase 8** | Docker Compose Containerization, GitHub Actions CI & Test Suite | ~1.5 hours |
| **Total** | | **~13.0 hours** |
