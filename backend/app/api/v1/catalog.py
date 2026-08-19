import json
import math
import os
from typing import Optional, List, Dict, Any, Tuple
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.core.config import settings
from backend.app.schemas.viewer import SearchResponse, SearchResultItem

router = APIRouter(prefix="/catalog", tags=["Viewer Catalogue API"])

"""
========================================================================================
ARCHITECTURAL RATIONALE: Published Catalogue vs Database Queries
========================================================================================
1. WHY READ ONLY FROM catalogue.json FOR THE VIEWER SURFACE:
   - Zero Database Load: Thousands of children browsing or streaming content hit only
     the pre-compiled static catalogue file or edge CDN/memory cache. The transactional
     PostgreSQL database is reserved strictly for content CMS editors.
   - Microsecond Response Times: The published catalogue is a single deterministic JSON
     file loaded with zero SQL join overhead.
   - Cache Coherence: All viewers receive identical, immutable snapshots of the streaming
     catalogue until an explicit, validated PublishRun is triggered by an admin.

2. WHEN TO SCALE TO FULL-TEXT SEARCH (PostgreSQL tsvector / Elasticsearch / Typesense):
   - Dataset Size: For small-to-medium catalogues (< 1,000 shows, < 50,000 episodes),
     in-memory linear filtering over the cached catalogue JSON executes in < 2 milliseconds
     with minimal RAM footprint (~2 MB).
   - Scaling Inflection Point (> 100,000 items): When the catalogue grows beyond 10,000+
     titles with rich transcripts, synopsis translations, and complex multi-token typo
     tolerance, search should be offloaded to:
       a) PostgreSQL `tsvector` with GIN indexes on a read-replica, or
       b) A dedicated search engine like Meilisearch, Typesense, or Elasticsearch, or
       c) Edge Search via Cloudflare Workers / Fastly KV reading compressed catalogue indexes.
========================================================================================
"""

from backend.app.storage import get_storage

def _load_live_catalogue() -> Dict[str, Any]:
    """Reads the live published catalogue.json from storage."""
    storage = get_storage()
    data_bytes = storage.get_bytes("catalogue.json")
    if data_bytes is None:
        data_bytes = storage.get_bytes("catalogue/catalogue.json")

    if data_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No catalogue has been published yet. Please publish the catalogue via the admin CMS."
        )

    try:
        return json.loads(data_bytes.decode("utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read published catalogue file: {str(e)}"
        )

# 1. GET /catalog (Live Published Catalogue)
@router.get("", response_model=Dict[str, Any])
@router.get("/published", response_model=Dict[str, Any])
def get_published_catalogue():
    """
    Returns the complete live published streaming catalogue.
    Used by the viewer UI for row browsing (Featured, Series, Minisodes, Songs).
    """
    return _load_live_catalogue()

# 2. GET /catalog/search (Server-side search against published catalogue)
@router.get("/search", response_model=SearchResponse)
def search_catalogue(
    q: Optional[str] = Query(None, description="Search term matching show title, episode title, synopsis, or category"),
    category: Optional[str] = Query(None, description="Filter by category tag"),
    language: Optional[str] = Query(None, description="Filter by available language ('en' or 'hi')"),
    section: Optional[str] = Query(None, description="Filter by section ('featured', 'series', 'minisodes', 'songs')"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Searches the live published catalogue server-side across shows and episodes.
    Composes all provided query parameters (q, category, language, section).
    """
    catalogue = _load_live_catalogue()
    all_shows: List[Dict[str, Any]] = []

    # Flatten shows across all sections (avoiding duplicates if a show appears in multiple rows)
    seen_ids = set()
    for sec in catalogue.get("sections", []):
        for show in sec.get("shows", []):
            show_id = show.get("id")
            if show_id not in seen_ids:
                seen_ids.add(show_id)
                all_shows.append(show)

    # Apply composable filters
    matched_results: List[SearchResultItem] = []
    q_clean = q.strip().lower() if q and q.strip() else None
    cat_clean = category.strip().lower() if category and category.strip() else None
    lang_clean = language.strip().lower() if language and language.strip() else None
    sec_clean = section.strip().lower() if section and section.strip() else None

    for show in all_shows:
        # 1. Section filter
        if sec_clean and show.get("section", "").lower() != sec_clean:
            continue

        # 2. Category filter
        show_cats = [c.lower() for c in show.get("categories", [])]
        if cat_clean and cat_clean not in show_cats:
            continue

        # 3. Language filter
        show_langs = [l.lower() for l in show.get("available_languages", [])]
        if lang_clean and lang_clean not in show_langs:
            continue

        # 4. Text Search (q) matching Show Title, Synopsis, Categories, or Episode Titles
        matched_ep_titles: List[str] = []
        if q_clean:
            title_match = q_clean in show.get("title", "").lower()
            synopsis_match = q_clean in show.get("synopsis", "").lower()
            cat_match = any(q_clean in c for c in show_cats)

            # Search across all regular seasons and episodes
            for s in show.get("seasons", []):
                for ep in s.get("episodes", []):
                    # Check collapsed title
                    if q_clean in ep.get("title", "").lower():
                        matched_ep_titles.append(ep.get("title"))
                    # Check language variants
                    for v in ep.get("variants", []):
                        if q_clean in v.get("episode_title", "").lower():
                            if v.get("episode_title") not in matched_ep_titles:
                                matched_ep_titles.append(v.get("episode_title"))

            # Search across trailers (Season 0)
            for tr in show.get("trailers", []):
                if q_clean in tr.get("title", "").lower():
                    matched_ep_titles.append(f"Trailer: {tr.get('title')}")
                for v in tr.get("variants", []):
                    if q_clean in v.get("episode_title", "").lower():
                        t_title = f"Trailer: {v.get('episode_title')}"
                        if t_title not in matched_ep_titles:
                            matched_ep_titles.append(t_title)

            # If q is provided and none matched -> skip show
            if not (title_match or synopsis_match or cat_match or len(matched_ep_titles) > 0):
                continue

        matched_results.append(SearchResultItem(
            id=show.get("id"),
            title=show.get("title"),
            slug=show.get("slug"),
            section=show.get("section"),
            categories=show.get("categories", []),
            synopsis=show.get("synopsis", ""),
            artwork=show.get("artwork", {}),
            available_languages=show.get("available_languages", []),
            total_episodes=show.get("total_episodes", 0),
            matched_episodes=matched_ep_titles
        ))

    # Pagination
    total = len(matched_results)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    paged_items = matched_results[offset : offset + page_size]

    return SearchResponse(
        query=q,
        category=category,
        language=language,
        section=section,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=paged_items
    )
