import json
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from backend.app.storage import get_storage

class CatalogService:
    @staticmethod
    def get_published_catalog() -> Dict[str, Any]:
        storage = get_storage()
        raw = storage.get("catalogue/catalogue.json")
        if not raw:
            raise HTTPException(status_code=404, detail="No catalogue published yet.")
        return json.loads(raw.decode("utf-8"))

    @staticmethod
    def search(
        q: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        section: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            catalog = CatalogService.get_published_catalog()
        except HTTPException:
            return {"query": q, "total_matches": 0, "results": []}

        q_lower = q.lower().strip() if q else None
        all_shows: List[Dict[str, Any]] = []
        seen = set()

        if catalog.get("featured"):
            all_shows.append(catalog["featured"])
            seen.add(catalog["featured"].get("id"))

        for sec in catalog.get("sections", []):
            for s in sec.get("shows", []):
                if s.get("id") not in seen:
                    all_shows.append(s)
                    seen.add(s.get("id"))

        results = []
        for show in all_shows:
            if section and show.get("section") != section:
                continue
            show_cats = [c.lower() for c in show.get("categories", [])]
            if category and category.lower() not in show_cats:
                continue
            show_langs = [l.lower() for l in show.get("available_languages", [])]
            if language and language.lower() not in show_langs:
                continue

            if q_lower:
                title_match = q_lower in show.get("title", "").lower()
                syn_match = q_lower in show.get("synopsis", "").lower()
                cat_match = any(q_lower in c for c in show_cats)
                ep_match = any(
                    q_lower in ep.get("title", "").lower() or any(q_lower in v.get("episode_title", "").lower() for v in ep.get("variants", []))
                    for season in show.get("seasons", [])
                    for ep in season.get("episodes", [])
                )
                if not (title_match or syn_match or cat_match or ep_match):
                    continue

            results.append(show)

        return {
            "query": q,
            "filters": {"category": category, "language": language, "section": section},
            "total_matches": len(results),
            "results": results
        }
