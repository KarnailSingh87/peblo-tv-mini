from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.core.config import settings
from backend.app.models.show import Show
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork
from backend.app.models.publish_run import PublishRun
from backend.app.schemas.catalog import (
    Catalogue, CatalogueSection, CatalogueShow, CatalogueSeason,
    CatalogueEpisode, CatalogueEpisodeVariant, PublishResponse
)
from backend.app.services.validation_service import ValidationService
from backend.app.storage import get_storage

class PublishService:
    @staticmethod
    def publish(db: Session, triggered_by: str) -> PublishResponse:
        report = ValidationService.audit_catalog(db)
        if not report.can_publish:
            blockers = [f"[{i.code}] {i.message}" for i in report.all_issues if i.severity == "blocking"]
            raise HTTPException(
                status_code=422,
                detail={"error": "Publish blocked due to validation issues.", "blockers": blockers}
            )

        storage = get_storage()
        last_run = db.query(PublishRun).filter(PublishRun.status == "success").order_by(PublishRun.version.desc()).first()
        new_version = (last_run.version + 1) if last_run else 1
        now_str = datetime.utcnow().isoformat() + "Z"

        try:
            published_shows = db.query(Show).filter(Show.status == "published").order_by(Show.title.asc()).all()
            all_art = db.query(Artwork).all()
            show_art_map: Dict[str, Dict[str, str]] = {}
            ep_art_map: Dict[str, Dict[str, str]] = {}
            for a in all_art:
                if a.entity_type == "show":
                    show_art_map.setdefault(a.entity_id, {})[a.artwork_type] = a.url
                elif a.entity_type == "episode":
                    ep_art_map.setdefault(a.entity_id, {})[a.artwork_type] = a.url

            shows_by_section: Dict[str, List[CatalogueShow]] = {sec: [] for sec in settings.ALLOWED_SECTIONS}
            total_episodes_count = 0

            for show in published_shows:
                if not show.section or show.section not in settings.ALLOWED_SECTIONS:
                    continue

                episodes = db.query(Episode).filter(Episode.show_id == show.id, Episode.status == "published").all()
                if not episodes:
                    continue

                seasons_map: Dict[int, Dict[str, List[Episode]]] = {}
                trailers_map: Dict[str, List[Episode]] = {}
                show_languages = set()

                for ep in episodes:
                    s_num = ep.season.season_number if ep.season else 1
                    cg = ep.content_group
                    show_languages.add(ep.language)

                    if s_num == 0:
                        trailers_map.setdefault(cg, []).append(ep)
                    else:
                        seasons_map.setdefault(s_num, {}).setdefault(cg, []).append(ep)

                # Build collapsed seasons
                cat_seasons: List[CatalogueSeason] = []
                for s_num in sorted(seasons_map.keys()):
                    cg_dict = seasons_map[s_num]
                    season_eps: List[CatalogueEpisode] = []

                    for cg, ep_list in sorted(cg_dict.items(), key=lambda x: x[1][0].episode_number):
                        ep_list.sort(key=lambda e: (0 if e.language == "en" else 1, e.language))
                        primary_ep = ep_list[0]

                        variants = [
                            CatalogueEpisodeVariant(
                                language=e.language,
                                episode_id=e.custom_id or str(e.id),
                                episode_title=e.episode_title,
                                duration_seconds=e.duration_seconds
                            )
                            for e in ep_list
                        ]

                        ep_art = {}
                        for e in ep_list:
                            k = e.custom_id or str(e.id)
                            if k in ep_art_map:
                                ep_art.update(ep_art_map[k])

                        season_eps.append(CatalogueEpisode(
                            content_group=cg,
                            episode_number=primary_ep.episode_number,
                            title=primary_ep.episode_title,
                            duration_seconds=primary_ep.duration_seconds or 0,
                            languages=sorted(list(set(e.language for e in ep_list))),
                            artwork=ep_art,
                            variants=variants
                        ))
                        total_episodes_count += 1

                    cat_seasons.append(CatalogueSeason(
                        season_number=s_num,
                        title=f"Season {s_num}",
                        episodes=season_eps
                    ))

                # Build trailers
                cat_trailers: List[CatalogueEpisode] = []
                for cg, ep_list in sorted(trailers_map.items(), key=lambda x: x[1][0].episode_number):
                    ep_list.sort(key=lambda e: (0 if e.language == "en" else 1, e.language))
                    primary_ep = ep_list[0]
                    variants = [
                        CatalogueEpisodeVariant(
                            language=e.language,
                            episode_id=e.custom_id or str(e.id),
                            episode_title=e.episode_title,
                            duration_seconds=e.duration_seconds
                        )
                        for e in ep_list
                    ]
                    ep_art = {}
                    for e in ep_list:
                        k = e.custom_id or str(e.id)
                        if k in ep_art_map:
                            ep_art.update(ep_art_map[k])

                    cat_trailers.append(CatalogueEpisode(
                        content_group=cg,
                        episode_number=primary_ep.episode_number,
                        title=primary_ep.episode_title,
                        duration_seconds=primary_ep.duration_seconds or 0,
                        languages=sorted(list(set(e.language for e in ep_list))),
                        artwork=ep_art,
                        variants=variants
                    ))

                shows_by_section[show.section].append(CatalogueShow(
                    id=show.id,
                    title=show.title,
                    slug=show.slug,
                    section=show.section,
                    categories=show.categories or [],
                    synopsis=show.synopsis or "",
                    artwork=show_art_map.get(str(show.id), {}),
                    available_languages=sorted(list(show_languages)),
                    total_episodes=sum(len(s.episodes) for s in cat_seasons),
                    seasons=cat_seasons,
                    trailers=cat_trailers
                ))

            # Build sections list
            sections: List[CatalogueSection] = []
            for sec in settings.ALLOWED_SECTIONS:
                s_list = shows_by_section.get(sec, [])
                if s_list:
                    sections.append(CatalogueSection(
                        section=sec,
                        title=sec.capitalize(),
                        shows=s_list
                    ))

            featured = shows_by_section.get("featured", [None])[0] or (sections[0].shows[0] if sections and sections[0].shows else None)
            total_shows = sum(len(s.shows) for s in sections)

            catalogue = Catalogue(
                version=new_version,
                published_at=now_str,
                total_shows=total_shows,
                total_episodes=total_episodes_count,
                featured=featured,
                sections=sections
            )

            raw_bytes = catalogue.model_dump_json(indent=2).encode("utf-8")
            live_url = storage.save_atomic(raw_bytes, "catalogue/catalogue.json", content_type="application/json")
            version_path = f"catalogue/catalogue_v{new_version}.json"
            storage.save(raw_bytes, version_path, content_type="application/json")

            run = PublishRun(
                published_at=datetime.utcnow(),
                triggered_by=triggered_by,
                status="success",
                show_count=total_shows,
                episode_count=total_episodes_count,
                version=new_version,
                file_path=version_path,
                metadata_json={"sections_count": len(sections)}
            )
            db.add(run)
            db.commit()

            return PublishResponse(
                success=True,
                version=new_version,
                published_at=now_str,
                shows_published=total_shows,
                episodes_published=total_episodes_count,
                message=f"Catalogue v{new_version} published atomically.",
                catalogue_url=live_url,
                publish_run_id=run.id
            )

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            failed_run = PublishRun(
                published_at=datetime.utcnow(),
                triggered_by=triggered_by,
                status="failed",
                version=new_version,
                error_message=str(e)
            )
            db.add(failed_run)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Publish failed: {str(e)}")
