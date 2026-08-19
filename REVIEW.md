# Peblo TV Mini — Senior Engineering Review

## Executive Summary
This comprehensive architectural and codebase audit evaluates the **Peblo TV Mini** implementation against all requirements defined in [`CHALLENGE.md`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/CHALLENGE.md).

The codebase exhibits strong architectural intent: proper separation between transactional CMS and static catalogue reads, role-based access control (RBAC), Pillow-based server-side artwork validation, pre-flight audit reporting, and atomic publish execution. However, a few critical integration gaps, schema contract mismatches, Docker build bugs, and legacy file duplications present severe risks to clean-state execution and viewer UI functionality.

---

## Detailed Requirements Matrix

| Requirement | Implemented? | Evidence | Risk | Suggested Fix |
|---|---|---|---|---|
| **Artwork validation is genuinely server-side** | **Yes** | [`ArtworkService.validate_artwork`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/services/artwork_service.py#L66-L140) reads binary bytes via Pillow (`PIL.Image.open`), decodes format, verifies integrity, checks dimensions and aspect ratio before persistence. | Low | None. Validation is robustly performed server-side with editor-friendly messages. |
| **200 KB limit** | **Yes** | [`ArtworkService.validate_artwork`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/services/artwork_service.py#L79-L84) enforces `file_size > max_bytes` (200 KB) and reports exact excess size in KB. | Low | None. Correctly enforced. |
| **Correct dimensions & aspect ratios** | **Yes** | [`ArtworkService.SPECS`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/services/artwork_service.py#L35-L63) tests `poster` (2:3, ~600×900), `banner` (16:9, ~1280×720), and `thumbnail` (16:9, ~640×360), rejecting orientation mismatches (e.g. horizontal poster) with actionable feedback. | Low | None. Verified in unit tests. |
| **Storage abstraction** | **Partial** | [`Storage`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/storage/base.py) ABC exists with [`LocalStorage`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/storage/local.py). However: 1) [`r2.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/storage/r2.py#L3) imports non-existent `StorageBackend` and implements wrong method signatures (`save` vs `upload`), 2) [`get_storage()`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/storage/__init__.py) ignores `settings.STORAGE_TYPE`, and 3) [`CataloguePublisher`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/services/publisher.py#L82) and [`catalog.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/api/v1/catalog.py#L39) bypass the storage interface with hardcoded `open()` on local paths. | **HIGH** | Refactor [`Storage`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/storage/base.py) to provide `save_atomic` and `get_bytes`, fix [`r2.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/storage/r2.py) inheritance/methods, wire `STORAGE_TYPE` switch in `get_storage()`, and use `get_storage()` across publisher and catalog reader. |
| **CRUD for shows/seasons/episodes** | **Yes** | Fully implemented in [`shows.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/api/v1/shows.py) and [`episodes.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/api/v1/episodes.py). Enforces positive duration, required artwork for published episodes, and assigned section for published shows. | Low | None. Covered by automated CRUD test suite. |
| **Validation report** | **Yes** | [`GET /api/v1/admin/validation-report`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/api/v1/admin.py#L15) and [`ValidationService.audit_catalog`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/services/validation_service.py) inspect all shows, seasons, episodes, and artwork, grouping by entity and categorizing into blocking vs warning with clear action hints. | Low | Ensure consistency in response schemas between backend and frontend CMS types. |
| **Editor / Admin permissions actually enforced** | **Yes** | [`deps.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/api/deps.py#L57-L73) implements `require_admin` and `require_editor_or_admin`. Publishing (`POST /admin/catalog/publish`) and publish history endpoints return HTTP 403 Forbidden for editor accounts. | Low | None. Verified in [`test_auth.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/tests/test_auth.py). |
| **content_group + language grouping** | **Yes** | Database uniqueness constraint `(content_group, language)` on [`Episode`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/models/entities.py#L155); [`CatalogueGenerator`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/services/catalog_generator.py#L108-L146) collapses language variants into single catalogue entries listing available languages. | Low | None. Verified in [`test_catalog_generator.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/tests/test_catalog_generator.py). |
| **Season 0 handling** | **Yes** | [`Season 0`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/models/entities.py#L93) is strictly partitioned as `trailers` list in [`CatalogueGenerator`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/services/catalog_generator.py#L155-L190); Viewer UI renders trailers in a dedicated bonus shelf separate from regular seasons. | Low | None. Verified in unit tests. |
| **Atomic publishing** | **Yes** | [`CataloguePublisher`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/services/publisher.py#L85-L110) writes to `.tmp` file, flushes & `fsync`s, and invokes POSIX `os.replace` to atomically replace live `catalogue.json`. | Medium | Needs to delegate through the storage abstraction rather than doing direct filesystem writes in the service. |
| **Failed publish preserves previous catalogue** | **Yes** | If validation fails or exception occurs during JSON compilation, no file replacement occurs. The previous live `catalogue.json` remains untouched, and a failed `PublishRun` is recorded in DB. | Low | None. Verified in [`test_publisher.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/tests/test_publisher.py). |
| **Idempotent publishing** | **Yes** | Repeated publish requests compile a deterministic snapshot, advance version number monotonically, and replace catalogue with identical deterministic payload. | Low | None. Verified in [`test_publisher.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/tests/test_publisher.py). |
| **Publish history** | **Yes** | [`GET /api/v1/admin/catalog/publish-runs`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/api/v1/admin.py#L64) returns ordered list of all historical publish attempts with version, user, timestamp, show/episode counts, status, and error details. | Low | None. Displayed in CMS Publish page. |
| **Viewer only accesses published catalogue** | **Yes** | Viewer client [`api.ts`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/frontend/viewer/src/services/api.ts) calls only `GET /catalog` and `GET /catalog/search`. Never touches CMS or database endpoints. | Low | None. Clean architectural boundary. |
| **Search/filter composition** | **Yes** | [`GET /catalog/search`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/api/v1/catalog.py#L69-L177) composes `q` (show title, episode titles in all languages, synopsis, category) with `category`, `language`, and `section` filters, supporting pagination. | Low | Fix minor field name discrepancy (`available_languages` vs `languages`) for frontend display badges. |
| **CMS loading / error / empty / permission states** | **Yes** | Handled in [`ShowListPage.tsx`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/frontend/cms/src/features/shows/ShowListPage.tsx), [`PublishPage.tsx`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/frontend/cms/src/features/publish/PublishPage.tsx), and [`Layout.tsx`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/frontend/cms/src/components/Layout.tsx) with skeletons, error boundaries, disabled publish button with tooltip reasons for editors, and empty notices. | Low | None. Usable and functional. |
| **Viewer loading / error / empty states** | **Partial** | Skeletons and empty states exist in [`HomePage.tsx`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/frontend/viewer/src/features/home/HomePage.tsx) and [`SearchPage.tsx`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/frontend/viewer/src/features/search/SearchPage.tsx). **However**, a schema mismatch on `catalog.sections` (backend returns `List[CatalogueSection]`, frontend expects `Record<string, CatalogueShow[]>`) causes the homepage and show detail page to render blank shelves or crash on variant dictionary access. | **HIGH** | Harmonize `Catalogue` JSON schema between backend and frontend (or adapt frontend `HomePage.tsx` and `ShowDetailPage.tsx` to handle array of sections and array of episode variants). |
| **Docker Compose works from clean state** | **Broken** | [`backend/Dockerfile`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/Dockerfile#L20) has `COPY data/ /app/data/`. The directory `data/` does not exist in the root context, causing `docker compose build` to immediately fail with build error. | **CRITICAL** | Remove `COPY data/ /app/data/` from `backend/Dockerfile` (the files `seed_shows.json` and `reference.json` are already copied separately from root). |
| **Migrations work** | **Yes** | Alembic migration [`0001_initial_schema.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/alembic/versions/0001_initial_schema.py) cleanly defines all tables, UUID primary keys, check constraints, foreign keys with cascade delete, and indexes. | Low | None. Runs successfully on clean PostgreSQL. |
| **Seed works** | **Yes** | [`backend/app/db/seed.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/db/seed.py) seeds 8 shows, seasons, episodes, and admin/editor users idempotently. Reports all deliberate imperfections in `seed_shows.json` (e.g. duplicate content groups, missing duration/artwork) without crashing. | Low | Fix hardcoded relative path in [`backend/tests/test_seed.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/tests/test_seed.py#L19) which looks for `../../data/seed_shows.json`. |
| **Tests pass** | **Partial** | 49 tests pass in pytest suite. 1 test fails due to incorrect file path in [`test_seed.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/tests/test_seed.py#L19), and [`test_catalog.py`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/tests/test_catalog.py) is a legacy test referencing old unexported schemas and outdated endpoints. | **HIGH** | Fix path in `test_seed.py` and update or remove obsolete `test_catalog.py` so the entire test suite executes 100% green. |
| **GitHub Actions works** | **Yes** | [`.github/workflows/ci.yml`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/.github/workflows/ci.yml) has linting, backend tests with PostgreSQL service container, frontend typecheck/builds, and Docker build validation. | Medium | Will fail at step 7a (Docker build) until `backend/Dockerfile` is fixed. |
| **.env.example complete** | **Yes** | [`.env.example`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/.env.example) covers all environment variables: DB, JWT, Storage, S3/R2 credentials, CORS, and VITE URLs. | Low | None. Complete and well documented. |
| **Health endpoint** | **Yes** | [`GET /health`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/main.py#L98) and [`GET /api/v1/health`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/backend/app/main.py#L106) probe both DB (`SELECT 1`) and storage accessibility, returning 503 if unhealthy. | Low | None. |
| **README honest and complete** | **Yes** | [`README.md`](file:///Users/harsh/Desktop/Full%20Stack%20%20Prompt%20Engineer/README.md) answers all Part E written questions (atomic publish, storage abstraction, search scale limits, static vs live DB trade-offs, omissions, AI log, alerting metric). | Low | None. Thorough and well structured. |

---

## 5 Highest-Risk Issues

### 1. `backend/Dockerfile` Build Failure (`COPY data/ /app/data/`)
- **Severity**: **CRITICAL**
- **Impact**: Clean-state `docker compose up --build` and GitHub Actions CI fail immediately during image build because the directory `data/` does not exist in the workspace root.
- **Root Cause**: An obsolete line `COPY data/ /app/data/` was left in `backend/Dockerfile` when data files were moved to the project root.

### 2. Frontend Viewer & Backend Catalogue Schema Contract Mismatch
- **Severity**: **HIGH**
- **Impact**: In the Viewer UI:
  1. `HomePage.tsx` attempts to read `catalog.sections?.[sec.key]`, expecting a dictionary, but backend `Catalogue.sections` is an Array (`List[CatalogueSection]`). Result: No show shelves are rendered on the homepage.
  2. `ShowDetailPage.tsx` accesses `epGroup.variants[preferredLang]` and `epGroup.available_languages`, but backend returns `variants: List[CatalogueEpisodeVariant]` and `languages: List[str]`. Result: JavaScript runtime `TypeError: undefined is not an object`, crashing the detail page.
- **Root Cause**: Backend and Frontend developed against slightly differing schema representations of the catalogue JSON.

### 3. Storage Abstraction Incomplete & Bypassed in Publisher / Catalog Service
- **Severity**: **HIGH**
- **Impact**: Setting `STORAGE_TYPE=r2` fails because:
  1. `backend/app/storage/r2.py` imports non-existent class `StorageBackend` and implements mismatched method names (`save` instead of `upload`, `get` instead of `get_bytes`).
  2. `backend/app/storage/__init__.py` never inspects `settings.STORAGE_TYPE`.
  3. `CataloguePublisher` and `GET /catalog` perform direct `open()` file I/O on the local disk instead of using the `Storage` interface.
- **Root Cause**: Incomplete interface synchronization between local disk and S3/R2 storage implementations.

### 4. Broken Test Suite (`test_seed.py` path error & legacy `test_catalog.py`)
- **Severity**: **MEDIUM-HIGH**
- **Impact**: Running `pytest` in CI or locally fails collection or assertions:
  1. `test_catalog.py` fails on import because of obsolete imports (`ValidationGroup` from `schemas`).
  2. `test_seed.py` fails assertion because it hardcodes `../../data/seed_shows.json` instead of locating `seed_shows.json` at root.
  3. `backend/app/main.py` executes `Base.metadata.create_all(bind=engine)` at module import time, requiring a live Postgres DB to even import `main.py` during unit testing without overriding `DATABASE_URL`.
- **Root Cause**: Legacy test file not updated to v1 router/service structure, and top-level side effects during module import.

### 5. Redundant Legacy Code & Duplicated Models in Backend
- **Severity**: **MEDIUM**
- **Impact**: The backend contains two parallel sets of models, schemas, and publishers:
  - Active: `backend/app/models/entities.py`, `backend/app/schemas/`, `backend/app/services/`
  - Legacy/Duplicate: `backend/app/models.py`, `backend/app/schemas.py`, `backend/app/publisher.py`, `backend/app/validator.py`, `backend/app/storage.py`, `backend/app/routers/`
  This creates confusion, accidental imports of obsolete logic, and maintenance hazards.
- **Root Cause**: Refactoring from flat files to modular directory structure left old files at `backend/app/` root.

---

## Proposed Fixes for the 5 Issues

1. **Fix `backend/Dockerfile` and `test_seed.py` paths**:
   - In `backend/Dockerfile`, remove `COPY data/ /app/data/`.
   - In `backend/app/db/seed.py` and `backend/tests/test_seed.py`, ensure resolution looks for `seed_shows.json` in the root workspace directory.

2. **Harmonize Catalogue Schema & Viewer UI**:
   - Update `Catalogue` schema or viewer frontend so `catalog.sections` and episode `variants` / `languages` contracts match seamlessly across backend and viewer React components (`HomePage.tsx`, `ShowDetailPage.tsx`, `SearchPage.tsx`, `types/index.ts`).

3. **Unify and Complete the Storage Abstraction**:
   - Align `Storage` ABC in `backend/app/storage/base.py` with `upload`, `delete`, `exists`, `get_url`, `get_bytes`, and `save_atomic`.
   - Fix `backend/app/storage/r2.py` to implement the updated `Storage` ABC.
   - Update `backend/app/storage/__init__.py` to instantiate `R2Storage` or `LocalStorage` based on `settings.STORAGE_TYPE`.
   - Update `CataloguePublisher` and `catalog.py` to use `get_storage()`.

4. **Fix Test Suite & Eliminate Module-Level DB Side Effects in `main.py`**:
   - Remove or migrate `backend/tests/test_catalog.py` to use active v1 endpoints and schemas.
   - Wrap `Base.metadata.create_all(bind=engine)` inside the FastAPI lifespan handler rather than running at raw import time, allowing clean testing with in-memory SQLite.

5. **Clean Up Legacy Duplicate Files**:
   - Safely remove or deprecate unused legacy root files (`backend/app/models.py`, `backend/app/schemas.py`, `backend/app/publisher.py`, `backend/app/validator.py`, `backend/app/storage.py`, `backend/app/database.py`, `backend/app/routers/`) and ensure all imports consistently point to `backend/app/models/entities.py`, `backend/app/schemas/`, `backend/app/services/`, and `backend/app/api/v1/`.
