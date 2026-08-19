from typing import List, Dict, Tuple, Any
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.entities import Show, Season, Episode, Artwork
from backend.app.schemas.validation import ValidationIssue, GroupedValidationIssues, ValidationReportResponse
from backend.app.storage import get_storage

class ValidationService:
    """
    Comprehensive Catalog Audit Engine.
    Scans database entities and identifies all publish-blocking errors and editorial warnings.
    """

    @classmethod
    def audit_catalog(cls, db: Session) -> ValidationReportResponse:
        grouped = GroupedValidationIssues(
            shows=[],
            seasons=[],
            episodes=[],
            artwork=[],
            other=[]
        )
        all_issues: List[ValidationIssue] = []

        storage = get_storage()
        shows = db.query(Show).all()
        episodes = db.query(Episode).all()
        artworks = db.query(Artwork).all()

        # 1. SHOW VALIDATION
        for show in shows:
            show_id_str = str(show.id)

            # Check 1: Published show without section
            if show.status == "published" and not show.section:
                issue = ValidationIssue(
                    code="SHOW_MISSING_SECTION",
                    severity="blocking",
                    entity_type="show",
                    entity_id=show_id_str,
                    title=show.title,
                    show_id=show_id_str,
                    show_title=show.title,
                    problem=f"Show '{show.title}' is marked published but has no homepage section assigned.",
                    action="Assign a valid section ('featured', 'series', 'minisodes', or 'songs') before publishing."
                )
                grouped.shows.append(issue)
                all_issues.append(issue)

            # Check 2: Invalid section value
            if show.section and show.section not in settings.ALLOWED_SECTIONS:
                issue = ValidationIssue(
                    code="INVALID_SECTION",
                    severity="blocking",
                    entity_type="show",
                    entity_id=show_id_str,
                    title=show.title,
                    show_id=show_id_str,
                    show_title=show.title,
                    problem=f"Show '{show.title}' has an invalid section '{show.section}'.",
                    action=f"Update section to one of the permitted values: {', '.join(settings.ALLOWED_SECTIONS)}."
                )
                grouped.shows.append(issue)
                all_issues.append(issue)

            # Check 3: Invalid categories
            for cat in (show.categories or []):
                if cat not in settings.ALLOWED_CATEGORIES:
                    issue = ValidationIssue(
                        code="INVALID_CATEGORY",
                        severity="blocking",
                        entity_type="show",
                        entity_id=show_id_str,
                        title=show.title,
                        show_id=show_id_str,
                        show_title=show.title,
                        problem=f"Show '{show.title}' contains unrecognized category '{cat}'.",
                        action=f"Remove '{cat}' and select from allowed categories: {', '.join(settings.ALLOWED_CATEGORIES)}."
                    )
                    grouped.shows.append(issue)
                    all_issues.append(issue)

            # Check 4: Draft show notice
            if show.status == "draft":
                issue = ValidationIssue(
                    code="SHOW_DRAFT_STATUS",
                    severity="warning",
                    entity_type="show",
                    entity_id=show_id_str,
                    title=show.title,
                    show_id=show_id_str,
                    show_title=show.title,
                    problem=f"Show '{show.title}' is currently in draft status (will not be published to viewers).",
                    action="Change status to 'published' when the show is ready to release."
                )
                grouped.shows.append(issue)
                all_issues.append(issue)

        # 2. SEASON VALIDATION
        seasons = db.query(Season).all()
        for s in seasons:
            season_id_str = str(s.id)
            ep_count = db.query(Episode).filter(Episode.season_id == s.id).count()
            if ep_count == 0:
                issue = ValidationIssue(
                    code="EMPTY_SEASON",
                    severity="warning",
                    entity_type="season",
                    entity_id=season_id_str,
                    title=s.title or f"Season {s.season_number}",
                    show_id=str(s.show_id),
                    show_title=s.show.title if s.show else "Unknown Show",
                    season_number=s.season_number,
                    problem=f"Season {s.season_number} of show '{s.show.title if s.show else ''}' contains 0 episodes.",
                    action="Add episodes to this season or remove the empty season."
                )
                grouped.seasons.append(issue)
                all_issues.append(issue)

        # 3. EPISODE VALIDATION & (content_group, language) UNIQUENESS
        cg_lang_tracker: Dict[Tuple[str, str], List[Episode]] = {}

        for ep in episodes:
            ep_id_str = ep.custom_id or str(ep.id)
            show_title = ep.show.title if ep.show else "Unknown Show"
            season_num = ep.season.season_number if ep.season else 1

            # Track (content_group, language)
            if ep.content_group and ep.language:
                key = (ep.content_group, ep.language)
                cg_lang_tracker.setdefault(key, []).append(ep)

            # Check 1: Invalid language
            if ep.language and ep.language not in settings.ALLOWED_LANGUAGES:
                issue = ValidationIssue(
                    code="INVALID_LANGUAGE",
                    severity="blocking",
                    entity_type="episode",
                    entity_id=ep_id_str,
                    title=ep.episode_title,
                    show_id=str(ep.show_id),
                    show_title=show_title,
                    season_number=season_num,
                    episode_number=ep.episode_number,
                    problem=f"Episode '{ep.episode_title}' has unsupported language '{ep.language}'.",
                    action=f"Change language to an allowed code ({', '.join(settings.ALLOWED_LANGUAGES)})."
                )
                grouped.episodes.append(issue)
                all_issues.append(issue)

            # Check 2: Published episode missing duration
            if ep.status == "published":
                if not ep.duration_seconds or ep.duration_seconds <= 0:
                    issue = ValidationIssue(
                        code="EPISODE_MISSING_DURATION",
                        severity="blocking",
                        entity_type="episode",
                        entity_id=ep_id_str,
                        title=ep.episode_title,
                        show_id=str(ep.show_id),
                        show_title=show_title,
                        season_number=season_num,
                        episode_number=ep.episode_number,
                        problem=f"Published episode '{ep.episode_title}' ({ep_id_str}) has no runtime duration.",
                        action="Add the episode duration in seconds before publishing."
                    )
                    grouped.episodes.append(issue)
                    all_issues.append(issue)

                # Check 3: Published episode missing required artwork
                has_uploaded_art = db.query(Artwork).filter(Artwork.episode_id == ep.id).first() is not None
                has_avail_list = bool(ep.artwork_available and len(ep.artwork_available) > 0)

                if not has_uploaded_art and not has_avail_list:
                    issue = ValidationIssue(
                        code="EPISODE_MISSING_ARTWORK",
                        severity="blocking",
                        entity_type="episode",
                        entity_id=ep_id_str,
                        title=ep.episode_title,
                        show_id=str(ep.show_id),
                        show_title=show_title,
                        season_number=season_num,
                        episode_number=ep.episode_number,
                        problem=f"Published episode '{ep.episode_title}' ({ep_id_str}) has no artwork available.",
                        action="Upload a 16:9 thumbnail before publishing."
                    )
                    grouped.episodes.append(issue)
                    all_issues.append(issue)
            else:
                issue = ValidationIssue(
                    code="EPISODE_DRAFT_STATUS",
                    severity="warning",
                    entity_type="episode",
                    entity_id=ep_id_str,
                    title=ep.episode_title,
                    show_id=str(ep.show_id),
                    show_title=show_title,
                    season_number=season_num,
                    episode_number=ep.episode_number,
                    problem=f"Episode '{ep.episode_title}' is in draft status (excluded from live catalogue).",
                    action="Set status to 'published' when the episode is ready."
                )
                grouped.episodes.append(issue)
                all_issues.append(issue)

        # Check 4: Duplicate (content_group, language) collisions
        for (cg, lang), ep_list in cg_lang_tracker.items():
            if len(ep_list) > 1:
                for ep in ep_list:
                    ep_id_str = ep.custom_id or str(ep.id)
                    issue = ValidationIssue(
                        code="DUPLICATE_CONTENT_GROUP_LANGUAGE",
                        severity="blocking",
                        entity_type="episode",
                        entity_id=ep_id_str,
                        title=ep.episode_title,
                        show_id=str(ep.show_id),
                        show_title=ep.show.title if ep.show else "Show",
                        problem=f"Episode '{ep.episode_title}' ({ep_id_str}) has duplicate content group '{cg}' with language '{lang}'.",
                        action="Ensure each audio language variant within a content group is strictly unique."
                    )
                    grouped.episodes.append(issue)
                    all_issues.append(issue)

        # 4. ARTWORK VALIDATION
        for art in artworks:
            art_id_str = str(art.id)
            # Check if file exists in storage
            if art.file_path and not storage.exists(art.file_path):
                issue = ValidationIssue(
                    code="ARTWORK_FILE_NOT_FOUND",
                    severity="blocking",
                    entity_type="artwork",
                    entity_id=art_id_str,
                    problem=f"Artwork asset '{art.artwork_type}' for {art.entity_type} '{art.show_id or art.episode_id}' is missing from storage at '{art.file_path}'.",
                    action="Re-upload the missing artwork asset."
                )
                grouped.artwork.append(issue)
                all_issues.append(issue)

        blocking_count = sum(1 for i in all_issues if i.severity == "blocking")
        warning_count = sum(1 for i in all_issues if i.severity == "warning")

        return ValidationReportResponse(
            can_publish=(blocking_count == 0),
            total_issues=len(all_issues),
            blocking_count=blocking_count,
            warning_count=warning_count,
            grouped_by_entity=grouped,
            all_issues=all_issues
        )
