import json
import os
import sys
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Ensure app package is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal, engine
from backend.app.models.entities import Base, Show, Season, Episode, User
from backend.app.core.security import get_password_hash

def run_seed(db: Session, json_path: str = None) -> Dict[str, Any]:
    """
    Idempotently seeds database from seed_shows.json.
    Reports all data integrity problems, preserves Season 0, and avoids silent data mutation.
    """
    if not json_path:
        candidates = [
            os.path.join(backend_dir, "..", "data", "seed_shows.json"),
            os.path.join(backend_dir, "data", "seed_shows.json"),
            os.path.abspath("data/seed_shows.json"),
            os.path.abspath("seed_shows.json")
        ]
        for c in candidates:
            if os.path.exists(c):
                json_path = os.path.abspath(c)
                break

    if not json_path or not os.path.exists(json_path):
        raise FileNotFoundError(f"seed_shows.json not found at '{json_path}'")

    with open(json_path, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    # Ensure schema exists
    target_engine = db.bind or engine
    Base.metadata.create_all(bind=target_engine)

    # Ensure default users exist
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(
            username="admin",
            email="admin@peblo.tv",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True
        ))
    if not db.query(User).filter(User.username == "editor").first():
        db.add(User(
            username="editor",
            email="editor@peblo.tv",
            hashed_password=get_password_hash("editor123"),
            role="editor",
            is_active=True
        ))
    db.commit()

    report = {
        "total_records_in_json": len(records),
        "shows_created": 0,
        "shows_updated": 0,
        "seasons_created": 0,
        "episodes_created": 0,
        "episodes_updated": 0,
        "validation_issues_found": [],
        "duplicate_conflicts": []
    }

    # Step 1: Ingest Shows
    shows_by_slug: Dict[str, Show] = {}
    show_records: Dict[str, List[Dict[str, Any]]] = {}

    for row in records:
        slug = row["slug"]
        show_records.setdefault(slug, []).append(row)

    for slug, row_list in show_records.items():
        sample = row_list[0]
        title = sample["show_title"]
        section = sample.get("section")
        categories = sample.get("categories", [])
        synopsis = sample.get("synopsis")
        status = sample.get("status", "draft")

        # Validate section against allowed constraints
        if not section:
            report["validation_issues_found"].append({
                "type": "SHOW_MISSING_SECTION",
                "show": title,
                "slug": slug,
                "status": status,
                "detail": f"Show '{title}' ({slug}) has section=null (status: '{status}')."
            })

        existing_show = db.query(Show).filter(Show.slug == slug).first()
        if not existing_show:
            existing_show = Show(
                title=title,
                slug=slug,
                section=section if section else None,
                categories=categories,
                synopsis=synopsis,
                status=status
            )
            db.add(existing_show)
            db.flush()
            report["shows_created"] += 1
        else:
            existing_show.title = title
            existing_show.section = section if section else None
            existing_show.categories = categories
            existing_show.synopsis = synopsis
            existing_show.status = status
            report["shows_updated"] += 1

        shows_by_slug[slug] = existing_show

    db.commit()

    # Step 2: Ingest Seasons (including Season 0 for Trailers)
    seasons_map: Dict[Tuple[str, int], Season] = {}
    for row in records:
        slug = row["slug"]
        show = shows_by_slug[slug]
        s_num = row.get("season_number", 1)

        key = (str(show.id), s_num)
        if key not in seasons_map:
            existing_season = db.query(Season).filter(
                Season.show_id == show.id,
                Season.season_number == s_num
            ).first()

            if not existing_season:
                title = "Trailers" if s_num == 0 else f"Season {s_num}"
                existing_season = Season(
                    show_id=show.id,
                    season_number=s_num,
                    title=title
                )
                db.add(existing_season)
                db.flush()
                report["seasons_created"] += 1

            seasons_map[key] = existing_season

    db.commit()

    # Step 3: Ingest Episodes and Report Data Issues
    seen_cg_lang: Dict[Tuple[str, str], str] = {}

    for row in records:
        custom_id = row.get("episode_id")
        slug = row["slug"]
        show = shows_by_slug[slug]
        s_num = row.get("season_number", 1)
        season = seasons_map[(str(show.id), s_num)]

        ep_title = row.get("episode_title")
        ep_num = row.get("episode_number", 1)
        duration = row.get("duration_seconds")
        language = row.get("language", "en")
        content_group = row.get("content_group")
        status = row.get("status", "draft")
        artwork_available = row.get("artwork_available", [])

        # Validate artwork & duration
        if status == "published" and not artwork_available:
            report["validation_issues_found"].append({
                "type": "EPISODE_MISSING_ARTWORK",
                "custom_id": custom_id,
                "title": ep_title,
                "show": show.title,
                "detail": f"Published episode '{ep_title}' ({custom_id}) has artwork_available=[]."
            })

        if status == "published" and (duration is None or duration <= 0):
            report["validation_issues_found"].append({
                "type": "EPISODE_INVALID_DURATION",
                "custom_id": custom_id,
                "title": ep_title,
                "show": show.title,
                "detail": f"Published episode '{ep_title}' ({custom_id}) has invalid duration {duration}."
            })

        # Check uniqueness of (content_group, language)
        cg_lang_key = (content_group, language)
        if cg_lang_key in seen_cg_lang:
            first_id = seen_cg_lang[cg_lang_key]
            report["duplicate_conflicts"].append({
                "type": "DUPLICATE_CONTENT_GROUP_LANGUAGE",
                "custom_id": custom_id,
                "conflicts_with": first_id,
                "content_group": content_group,
                "language": language,
                "title": ep_title,
                "detail": f"Episode '{custom_id}' has duplicate (content_group='{content_group}', language='{language}'), conflicting with '{first_id}'."
            })
            continue
        else:
            seen_cg_lang[cg_lang_key] = custom_id

        # Query existing episode by custom_id
        existing_ep = db.query(Episode).filter(Episode.custom_id == custom_id).first() if custom_id else None

        if not existing_ep:
            # Check if (content_group, language) already exists in database
            ep_by_cg = db.query(Episode).filter(
                Episode.content_group == content_group,
                Episode.language == language
            ).first()

            if ep_by_cg:
                # Collision with an already seeded episode
                report["duplicate_conflicts"].append({
                    "type": "DB_DUPLICATE_CONTENT_GROUP_LANGUAGE",
                    "custom_id": custom_id,
                    "existing_id": ep_by_cg.custom_id,
                    "content_group": content_group,
                    "language": language,
                    "detail": f"Database already contains episode with content_group='{content_group}', language='{language}' (custom_id='{ep_by_cg.custom_id}')."
                })
                continue

            new_ep = Episode(
                custom_id=custom_id,
                show_id=show.id,
                season_id=season.id,
                episode_number=ep_num,
                episode_title=ep_title,
                duration_seconds=duration,
                language=language,
                content_group=content_group,
                status=status,
                artwork_available=artwork_available
            )
            db.add(new_ep)
            report["episodes_created"] += 1
        else:
            existing_ep.show_id = show.id
            existing_ep.season_id = season.id
            existing_ep.episode_number = ep_num
            existing_ep.episode_title = ep_title
            existing_ep.duration_seconds = duration
            existing_ep.language = language
            existing_ep.content_group = content_group
            existing_ep.status = status
            existing_ep.artwork_available = artwork_available
            report["episodes_updated"] += 1

    db.commit()

    return report

def main():
    with SessionLocal() as db:
        print("Starting Peblo TV Mini database seeding...")
        report = run_seed(db)
        print("\n================ SEED EXECUTION REPORT ================")
        print(f"Total input JSON rows: {report['total_records_in_json']}")
        print(f"Shows:    {report['shows_created']} created, {report['shows_updated']} updated")
        print(f"Seasons:  {report['seasons_created']} created")
        print(f"Episodes: {report['episodes_created']} created, {report['episodes_updated']} updated")

        if report["duplicate_conflicts"]:
            print(f"\n[!] Duplicate (content_group, language) conflicts detected ({len(report['duplicate_conflicts'])}):")
            for c in report["duplicate_conflicts"]:
                print(f"  - [{c['type']}] {c['detail']}")

        if report["validation_issues_found"]:
            print(f"\n[!] Data validation issues detected ({len(report['validation_issues_found'])}):")
            for v in report["validation_issues_found"]:
                print(f"  - [{v['type']}] {v['detail']}")
        print("========================================================\n")

if __name__ == "__main__":
    main()
