# Peblo TV Mini — Data Analysis & Schema Mapping Report

This document presents a comprehensive, evidence-based analysis of the provided dataset (`seed_shows.json`) against reference constraints (`reference.json`), identifies data anomalies, outlines core business rules, and specifies the PostgreSQL relational schema mapping.

---

## 1. Discovered Dataset Structure

The dataset (`seed_shows.json`) consists of **95 flat JSON records** where each record represents a single language-specific episode or trailer alongside its parent show metadata:

| Field Name | Type | Level | Description / Constraints |
|---|---|---|---|
| `episode_id` | String | Episode | Unique identifier string (e.g., `"ep_0001"`, `"ep_9001"`) |
| `show_title` | String | Show | Display title of the parent show |
| `slug` | String | Show | URL-safe identifier for the show (e.g., `"motis-many-lives"`) |
| `section` | String \| Null | Show | Homepage section (`"featured"`, `"series"`, `"minisodes"`, `"songs"`, or `null`) |
| `categories` | Array[String] | Show | Educational tags (subset of 15 allowed categories) |
| `synopsis` | String | Show | Summary description of the show |
| `season_number` | Integer | Season | Season index (`0` reserved for trailers; `1..N` for regular seasons) |
| `episode_number` | Integer | Episode | 1-based order within the season |
| `episode_title` | String | Episode | Title in the specific audio language |
| `duration_seconds`| Integer | Episode | Runtime in seconds |
| `language` | String | Episode | Audio track language code (`"en"` or `"hi"`) |
| `content_group` | String | Episode | Canonical grouping key linking multilingual versions of the same episode |
| `status` | String | Episode/Show | Publishing workflow state (`"draft"` or `"published"`) |
| `artwork_available`| Array[String] | Episode | Available image types (`"poster"`, `"banner"`, `"thumbnail"`) |

---

## 2. Shows, Seasons & Content Hierarchy

There are **8 unique shows** in the seed catalog:

| Show Title | Slug | Section | Status | Seasons | Ep Count | Categories |
|---|---|---|---|---|---|---|
| **Moti's Many Lives** | `motis-many-lives` | `featured` | `published` | `0`, `1` | 18 | `adventure`, `india`, `friendship` |
| **Tiny Tales by Banyan Dadi** | `tiny-tales-by-banyan-dadi` | `series` | `published` | `0`, `1` | 17 | `folk`, `stories`, `values` |
| **Discover India with Moti** | `discover-india-with-moti` | `minisodes` | `published` | `1` | 10 | `travel`, `india`, `learning` |
| **Peblo Songs** | `peblo-songs` | `songs` | `published` | `1` | 16 | `music`, `singalong`, `learning` |
| **Peblo Songs — Lyrical** | `peblo-songs-lyrical` | `songs` | `published` | `1` | 10 | `music`, `reading`, `singalong` |
| **Curious Cubs** | `curious-cubs` | `series` | `published` | `1` | 8 | `science`, `nature`, `learning` |
| **Number Nest** | `number-nest` | `series` | Mixed (`draft`/`pub`) | `1` | 8 | `maths`, `learning`, `values` |
| **Rhyme Rangers** | `rhyme-rangers` | `null` | `draft` | `1` | 8 | `language`, `singalong`, `learning` |

---

## 3. Important Conventions & Rules

1. **Multilingual Collapsing via `content_group`**:
   - Episodes sharing the exact same `content_group` represent language variants of the same creative episode.
   - When building the published catalogue, these must collapse into a single catalogue entry listing its available `languages: ["en", "hi"]` and nested `variants` objects.
2. **Season 0 Trailer Isolation**:
   - `season_number: 0` is strictly reserved for promotional trailers.
   - In the viewer UI, Season 0 is not rendered as a regular numbered season but surfaced in a dedicated **"Trailers & Extras"** drawer/modal.
3. **Reference Constraints (`reference.json`)**:
   - **Allowed Sections (4)**: `featured`, `series`, `minisodes`, `songs`
   - **Allowed Categories (15)**: `adventure`, `folk`, `friendship`, `india`, `language`, `learning`, `maths`, `music`, `nature`, `reading`, `science`, `singalong`, `stories`, `travel`, `values`
   - **Allowed Languages (2)**: `en`, `hi`
   - **Artwork Specifications (3)**:
     - `poster`: Aspect ratio `2:3` (target ~600×900px, max 200 KB)
     - `banner`: Aspect ratio `16:9` (target ~1280×720px, max 200 KB)
     - `thumbnail`: Aspect ratio `16:9` (target ~640×360px, max 200 KB)

---

## 4. Validation Issues & Data Imperfections Found

The seed data contains intentional real-world imperfections that our validation engine detects:

### 🚨 Blocker 1: Missing Artwork on Published Episode
- **Location**: Episode `ep_0036` (*"The Midnight Market"* in *"Discover India with Moti"*, Season 1, Episode 4).
- **Issue**: `artwork_available: []` while `status: "published"`.
- **Resolution**: Content editors must upload at least a 16:9 thumbnail before catalog publishing can proceed.

### 🚨 Blocker 2: Duplicate `(content_group, language)` Pair
- **Location**: Show *"Moti's Many Lives"*, Season 1, Episode 2.
- **Records**:
  - `ep_0004`: `content_group: "motis-many-lives-s01e02"`, `language: "hi"`, title: *"Rain on the Roof"*
  - `ep_9001`: `content_group: "motis-many-lives-s01e02"`, `language: "hi"`, title: *"The Lost Kite (v2)"*
- **Issue**: Two distinct episode records claim the same audio track in the same content group.
- **Resolution**: Must be flagged by pre-publish audit to prevent nondeterministic language routing.

### ⚠️ Warning / Edge Case 3: Draft Show Without Assigned Section
- **Location**: Show *"Rhyme Rangers"*.
- **Issue**: `section: null` across all 8 episodes with `status: "draft"`.
- **Resolution**: Allowed while in draft, but must block transition to `status: "published"` until an editor selects one of the 4 allowed sections.

---

## 5. PostgreSQL Relational Schema Mapping

To eliminate data redundancy (flattening show/season metadata repeated across 95 rows) and enforce relational integrity, the seed data maps to normalized PostgreSQL tables:

```
┌───────────────────────────────────────────────────────────┐
│                           shows                           │
├───────────────────────────────────────────────────────────┤
│ id (PK, SERIAL)                                           │
│ title (VARCHAR(255), NOT NULL)                            │
│ slug (VARCHAR(255), UNIQUE, INDEX)                        │
│ section (VARCHAR(50), NULLABLE)                           │
│ categories (JSONB / JSON, NOT NULL)                       │
│ synopsis (TEXT)                                           │
│ status (VARCHAR(20), DEFAULT 'draft')                     │
│ created_at / updated_at (TIMESTAMP)                       │
└─────────────────────────────┬─────────────────────────────┘
                              │ 1:N
                              ▼
┌───────────────────────────────────────────────────────────┐
│                          seasons                          │
├───────────────────────────────────────────────────────────┤
│ id (PK, SERIAL)                                           │
│ show_id (FK -> shows.id, ON DELETE CASCADE)               │
│ season_number (INT, NOT NULL) [0 for Trailers, 1..N]       │
│ title (VARCHAR(255))                                      │
│ created_at / updated_at (TIMESTAMP)                       │
│ UNIQUE(show_id, season_number)                            │
└─────────────────────────────┬─────────────────────────────┘
                              │ 1:N
                              ▼
┌───────────────────────────────────────────────────────────┐
│                         episodes                          │
├───────────────────────────────────────────────────────────┤
│ id (PK, SERIAL)                                           │
│ custom_id (VARCHAR(50), INDEX) [e.g., "ep_0001"]          │
│ show_id (FK -> shows.id, ON DELETE CASCADE)               │
│ season_id (FK -> seasons.id, ON DELETE CASCADE)           │
│ episode_number (INT, NOT NULL)                            │
│ episode_title (VARCHAR(255), NOT NULL)                    │
│ duration_seconds (INT, NULLABLE)                          │
│ language (VARCHAR(10), NOT NULL) ['en' | 'hi']            │
│ content_group (VARCHAR(100), INDEX, NOT NULL)             │
│ status (VARCHAR(20), DEFAULT 'draft')                     │
│ artwork_available (JSONB / JSON, DEFAULT '[]')            │
│ created_at / updated_at (TIMESTAMP)                       │
│ INDEX(content_group, language)                            │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│                          artwork                          │
├───────────────────────────────────────────────────────────┤
│ id (PK, SERIAL)                                           │
│ entity_type (VARCHAR(20)) ['show' | 'episode']            │
│ entity_id (VARCHAR(50), INDEX)                            │
│ artwork_type (VARCHAR(20)) ['poster'|'banner'|'thumbnail']│
│ file_path (VARCHAR(500), NOT NULL)                        │
│ url (VARCHAR(500), NOT NULL)                              │
│ width (INT), height (INT), file_size_bytes (INT)          │
│ mime_type (VARCHAR(50))                                   │
│ UNIQUE(entity_type, entity_id, artwork_type)              │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│                       publish_runs                        │
├───────────────────────────────────────────────────────────┤
│ id (PK, SERIAL)                                           │
│ published_at (TIMESTAMP, DEFAULT NOW())                   │
│ triggered_by (VARCHAR(100))                               │
│ status (VARCHAR(20)) ['success' | 'failed']               │
│ show_count (INT), episode_count (INT), version (INT)      │
│ file_path (VARCHAR(500)), error_message (TEXT)            │
│ metadata_json (JSONB / JSON)                              │
└───────────────────────────────────────────────────────────┘
```

---

## 6. Seed Ingestion Strategy

1. **Group by Show**: Extract unique `(show_title, slug, section, synopsis, categories)` and insert into `shows`. If `section` is null or empty, store as `null`.
2. **Upsert Seasons**: For each show, ensure `Season 0` (Trailers) and `Season 1` are created in `seasons`.
3. **Insert Episodes**: Insert all 95 episode entries linking to their respective `show_id` and `season_id`. Preserve `custom_id` (`"ep_0001"`), `content_group`, and `artwork_available`.
4. **Seed Artwork**: Map initial sample images in `assets/` to their respective show/episode records.
