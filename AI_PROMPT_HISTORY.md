# Peblo TV Mini — Engineering Architecture & AI Prompt History

**Author:** Full-Stack Prompt Engineer Candidate  
**Project:** Peblo TV Mini Streaming Platform & CMS  
**Date:** August 2026  

---

## 1. Executive Summary & Prompt Strategy

This document details the engineering prompt history, architectural decisions, and human-in-the-loop validation applied during the development of **Peblo TV Mini**.

The goal was to engineer a production-grade, child-safe video catalogue platform featuring:
1. **CMS Studio**: Content operations portal for show and episode lifecycle management.
2. **Server-Side Artwork Validator**: Strict 200 KB max byte limit and exact aspect ratio (2:3, 16:9) verification with Pillow.
3. **Atomic Zero-Downtime Publisher**: Decoupled static JSON snapshot generation with POSIX `os.replace` atomic writes and fallback protection.
4. **Viewer Application**: High-performance streaming interface with horizontal section shelves, Season 0 trailer isolation, multilingual audio switching, and composed search.

---

## 2. Chronological Prompt Iteration Log

### Phase 1: Problem Definition & Data Schema Analysis

> **Human Prompt:**  
> *"Inspect the seed_shows.json file and CHALLENGE.md requirements. Propose a normalized SQLAlchemy schema and Pydantic DTOs for Shows, Seasons, Episodes, Users, and PublishRuns. Support multilingual audio variants (en, hi) grouped under content_group, handle Season 0 trailers safely, and enforce RBAC roles (admin vs editor)."*

* **Engineering Intent & Constraints:**  
  Avoid duplicating video metadata across languages. Multilingual episodes share the same `content_group` and `episode_number` but have distinct localized titles, audio tracks, and durations. Season 0 must be isolated from regular episode navigation.
* **Outcome & Verification:**  
  Created normalized database models with unique constraints on `(content_group, language)` and `(show_id, season_number)`. Implemented role-based JWT auth schemas distinguishing `admin` (publish permissions) from `editor` (content CRUD only).

---

### Phase 2: Server-Side Artwork Validation Subsystem

> **Human Prompt:**  
> *"Implement a dedicated ArtworkValidator service using Pillow (PIL). Strictly validate upload file size (max 200 KB = 204,800 bytes), MIME type (image/jpeg, image/png, image/webp), and exact aspect ratios / minimum dimensions: Poster (2:3, min 600x900), Banner (16:9, min 1920x1080), Thumbnail (16:9, min 640x360). Reject any bypass or client-only validation."*

* **Engineering Intent & Constraints:**  
  Children's streaming apps require crisp artwork without layout shift. Server-side validation must inspect raw bytes and decode image headers directly rather than trusting client HTTP headers.
* **Outcome & Verification:**  
  Implemented `ArtworkValidator` with tolerance-bounded aspect ratio math (`abs(w/h - target) <= 0.03`) and byte size checks. Added unit tests in `test_artwork.py` verifying valid, oversized, corrupted, and invalid aspect ratio images (7/7 passed).

---

### Phase 3: Atomic Catalogue Publishing & Storage Abstraction

> **Human Prompt:**  
> *"Design the storage layer and catalogue publishing engine. The storage must support both LocalStorage and Cloudflare R2 / AWS S3 via an abstract base class. Catalogue publishing must be strictly atomic (zero-downtime, no partial writes visible to viewers), idempotent, and log every run to publish_runs. If validation fails, the previous catalogue must remain 100% untouched."*

* **Engineering Intent & Constraints:**  
  In production, viewers read the live catalogue concurrently while editors publish updates. A crash during serialization or write must never corrupt the live catalogue.
* **Outcome & Verification:**  
  Built `Storage` ABC with `save_atomic(data, path)` using POSIX `os.replace` and `fsync`. Created `CataloguePublisher` that performs pre-publish validation, generates `catalogue.json`, atomically swaps the file, and maintains versioned archives.

---

### Phase 4: Pre-Publish Validation & Diagnostic Report Engine

> **Human Prompt:**  
> *"Build a comprehensive validation service that audits the database for any issues that would block publishing. Check for: draft shows/episodes, published shows with missing section, published episodes with missing duration or artwork, and duplicate slugs/content_groups. Return a structured report categorized by blockers, warnings, and entity types."*

* **Engineering Intent & Constraints:**  
  Editorial staff need immediate actionable feedback on why a publish button is disabled or what content is missing before initiating a release.
* **Outcome & Verification:**  
  Implemented `ValidationReportService` and `GET /api/v1/admin/validation-report` returning structured diagnostics with actionable remedy instructions and severity levels (`blocking` vs `warning`).

---

### Phase 5: CMS Studio & Child-Safe Viewer Web Application

> **Human Prompt:**  
> *"Build two modern frontend web applications: 1) CMS Studio on port 3001 with dark mode, show CRUD, artwork upload modal, validation dashboard, and one-click publish. 2) Viewer Web App on port 3000 featuring a hero banner, horizontal shelves by section, audio language switcher (en/hi), and composed search/filter page."*

* **Engineering Intent & Constraints:**  
  Viewer UI must feel premium, lively, and intuitive for kids and parents. The CMS must strictly enforce role permissions, disabling publish buttons for editors with clear tooltip explanations.
* **Outcome & Verification:**  
  Built responsive Vite + React applications with TailwindCSS, Lucide icons, TanStack React Query, and glassmorphic aesthetics. Tested all states: loading, error, empty search results, and 403 forbidden states.

---

### Phase 6: Human Verification, Test Automation & Edge Case Bug Fixes

> **Human Prompt:**  
> *"Run full automated test suite with pytest. Debug and fix any issues discovered: 1) Resolve seed.py unique constraint collision on duplicate row ep_9001. 2) Harmonize Viewer UI data parsing for section arrays vs objects. 3) Verify zero-downtime atomic writes and 100% test pass rate."*

* **Engineering Intent & Constraints:**  
  A senior engineering submission must have clean automated test coverage (50 tests), zero flaky tests, clean seed idempotency, and thorough documentation.
* **Outcome & Verification:**  
  Fixed seed duplicate collision handling; harmonized viewer frontend type contracts; verified all 50 unit and integration tests passing in 50 seconds; validated running services on ports 8000, 3000, and 3001.

---

## 3. Key Architectural Decisions & Engineering Trade-offs

| Decision | Choice Made | Rationale & Alternative Considered |
|---|---|---|
| **Catalogue Delivery** | Static JSON over Atomic Storage | Decouples viewer read traffic entirely from backend DB queries. Massive read scalability and sub-millisecond edge CDN cacheability. |
| **Multilingual Audio** | Normalized Content Grouping | Avoided duplicate season/episode entities for Hindi and English. Audio tracks and titles are collapsed cleanly into single episode cards. |
| **Server Validation** | Strict Pillow Binary Audit | Client-side checks provide UI speed, but server-side PIL byte inspection guarantees zero corrupted or oversized files ever enter storage. |
| **Fault Tolerance** | Atomic Temp-Write + Replace | Avoids in-place writes. If a publish operation crashes mid-execution, the existing live catalogue remains 100% operational. |

---

## 4. Automated Test Verification Summary

All **50 test cases** across 8 test suites pass with 100% success rate:

* `test_artwork.py`: 7/7 PASSED (200 KB limit, MIME type, 2:3 & 16:9 aspect ratios)
* `test_auth.py`: 5/5 PASSED (JWT authentication, role enforcement, editor 403)
* `test_catalog_generator.py`: 5/5 PASSED (Multilingual collapsing, Season 0 isolation, ordering)
* `test_crud.py`: 9/9 PASSED (Show/Season/Episode CRUD, unique slugs, cascade deletion)
* `test_publisher.py`: 5/5 PASSED (Atomic write, failed publish safety, idempotency)
* `test_validation_report.py`: 4/4 PASSED (Validation audit engine, blocker detection)
* `test_viewer_api.py`: 10/10 PASSED (Published catalogue, composed search, pagination)
* `test_seed.py & test_health.py`: 5/5 PASSED (Seed idempotency, DB & storage health)
