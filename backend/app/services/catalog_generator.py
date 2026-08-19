from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.entities import Show, Season, Episode, Artwork
from backend.app.schemas.catalog import (
    Catalogue, CatalogueSection, CatalogueShow, CatalogueSeason,
    CatalogueEpisode, CatalogueEpisodeVariant
)
from backend.app.services.validation_service import ValidationService

class CatalogueGenerationError(Exception):
    def __init__(self, message: str, blockers: List[str] = None):
        super().__init__(message)
        self.blockers = blockers or []

class CatalogueGenerator:
    """
    Pure catalogue compilation service.
    Transforms published relational database content into a deterministic Netflix-style catalogue JSON structure.
    Does NOT mutate database records during generation.
    """

    @classmethod
    def generate_catalogue_dict(cls, db: Session, version: int = 1, check_validation: bool = True) -> Dict[str, Any]:
        catalogue_obj = cls.generate_catalogue(db, version=version, check_validation=check_validation)
        return catalogue_obj.model_dump()

    @classmethod
    def generate_catalogue(cls, db: Session, version: int = 1, check_validation: bool = True) -> Catalogue:
        # Step 1: Pre-generation validation audit
        if check_validation:
            report = ValidationService.audit_catalog(db)
            if not report.can_publish:
                blocker_msgs = [f"[{i.code}] {i.problem}" for i in report.all_issues if i.severity == "blocking"]
                raise CatalogueGenerationError(
                    f"Catalogue generation blocked: {len(blocker_msgs)} data integrity issues must be resolved.",
                    blockers=blocker_msgs
                )

        now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Step 2: Fetch artwork mappings
        artworks = db.query(Artwork).all()
        show_art_map: Dict[str, Dict[str, str]] = {}
        ep_art_map: Dict[str, Dict[str, str]] = {}

        for art in artworks:
            if art.show_id:
                show_art_map.setdefault(str(art.show_id), {})[art.artwork_type] = art.url
            elif art.episode_id:
                ep_art_map.setdefault(str(art.episode_id), {})[art.artwork_type] = art.url

        # Step 3: Fetch ONLY published shows
        published_shows = (
            db.query(Show)
            .filter(Show.status == "published")
            .order_by(Show.title.asc(), Show.slug.asc())
            .all()
        )

        shows_by_section: Dict[str, List[CatalogueShow]] = {
            sec: [] for sec in settings.ALLOWED_SECTIONS
        }
        total_episodes_counter = 0

        for show in published_shows:
            # Skip shows with unassigned or invalid sections
            if not show.section or show.section not in settings.ALLOWED_SECTIONS:
                continue

            # Fetch ONLY published episodes for this show
            published_eps = (
                db.query(Episode)
                .join(Season, Episode.season_id == Season.id)
                .filter(Episode.show_id == show.id, Episode.status == "published")
                .order_by(Season.season_number.asc(), Episode.episode_number.asc(), Episode.language.asc())
                .all()
            )

            if not published_eps:
                continue

            # Partition episodes into Regular Seasons vs Season 0 (Trailers)
            seasons_map: Dict[int, Dict[str, List[Episode]]] = {}
            trailers_map: Dict[str, List[Episode]] = {}
            available_show_languages = set()

            for ep in published_eps:
                s_num = ep.season.season_number if ep.season else 1
                cg = ep.content_group
                available_show_languages.add(ep.language)

                if s_num == 0:
                    # Season 0 is strictly trailer content
                    trailers_map.setdefault(cg, []).append(ep)
                else:
                    # Regular viewer seasons (Season 1..N)
                    seasons_map.setdefault(s_num, {}).setdefault(cg, []).append(ep)

            # Build collapsed regular seasons
            catalogue_seasons: List[CatalogueSeason] = []
            for s_num in sorted(seasons_map.keys()):
                cg_dict = seasons_map[s_num]
                season_episodes: List[CatalogueEpisode] = []

                # Deterministically sort content groups by minimum episode number and content_group key
                sorted_cg_items = sorted(
                    cg_dict.items(),
                    key=lambda item: (item[1][0].episode_number, item[0])
                )

                for cg, ep_list in sorted_cg_items:
                    # Deterministically sort variants: 'en' first, then alphabetical by language
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

                    # Aggregate artwork
                    art_dict = {}
                    for e in ep_list:
                        eid_str = str(e.id)
                        if eid_str in ep_art_map:
                            art_dict.update(ep_art_map[eid_str])
                        if e.custom_id and e.custom_id in ep_art_map:
                            art_dict.update(ep_art_map[e.custom_id])

                    season_episodes.append(CatalogueEpisode(
                        content_group=cg,
                        episode_number=primary_ep.episode_number,
                        title=primary_ep.episode_title,
                        duration_seconds=primary_ep.duration_seconds or 0,
                        languages=sorted(list(set(e.language for e in ep_list))),
                        artwork=art_dict,
                        variants=variants
                    ))
                    total_episodes_counter += 1

                catalogue_seasons.append(CatalogueSeason(
                    season_number=s_num,
                    title=f"Season {s_num}",
                    episodes=season_episodes
                ))

            # Build collapsed trailers (Season 0)
            catalogue_trailers: List[CatalogueEpisode] = []
            sorted_trailer_cg = sorted(
                trailers_map.items(),
                key=lambda item: (item[1][0].episode_number, item[0])
            )

            for cg, ep_list in sorted_trailer_cg:
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

                art_dict = {}
                for e in ep_list:
                    eid_str = str(e.id)
                    if eid_str in ep_art_map:
                        art_dict.update(ep_art_map[eid_str])

                catalogue_trailers.append(CatalogueEpisode(
                    content_group=cg,
                    episode_number=primary_ep.episode_number,
                    title=primary_ep.episode_title,
                    duration_seconds=primary_ep.duration_seconds or 0,
                    languages=sorted(list(set(e.language for e in ep_list))),
                    artwork=art_dict,
                    variants=variants
                ))

            show_artwork = show_art_map.get(str(show.id), {})

            cat_show = CatalogueShow(
                id=hash(show.slug) & 0x7FFFFFFF,  # Deterministic integer ID
                title=show.title,
                slug=show.slug,
                section=show.section,
                categories=sorted(show.categories or []),
                synopsis=show.synopsis or "",
                artwork=show_artwork,
                available_languages=sorted(list(available_show_languages)),
                total_episodes=sum(len(s.episodes) for s in catalogue_seasons),
                seasons=catalogue_seasons,
                trailers=catalogue_trailers
            )

            shows_by_section[show.section].append(cat_show)

        # Step 4: Assemble ordered sections
        sections_list: List[CatalogueSection] = []
        for sec_name in settings.ALLOWED_SECTIONS:
            sec_shows = shows_by_section.get(sec_name, [])
            if sec_shows:
                # Deterministically sort shows within section by title
                sec_shows.sort(key=lambda s: (s.title, s.slug))
                sections_list.append(CatalogueSection(
                    section=sec_name,
                    title=sec_name.capitalize(),
                    shows=sec_shows
                ))

        # Featured banner show (first show in featured section or first available show)
        featured_show = None
        if shows_by_section.get("featured"):
            featured_show = shows_by_section["featured"][0]
        elif sections_list and sections_list[0].shows:
            featured_show = sections_list[0].shows[0]

        total_shows_count = sum(len(s.shows) for s in sections_list)

        return Catalogue(
            version=version,
            published_at=now_iso,
            total_shows=total_shows_count,
            total_episodes=total_episodes_counter,
            featured=featured_show,
            sections=sections_list
        )
