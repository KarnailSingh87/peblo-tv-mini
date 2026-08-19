import pytest
from backend.app.models.entities import Show, Season, Episode, Artwork
from backend.app.services.validation_service import ValidationService

def test_validation_report_catches_all_blockers(client, auth_headers):
    # Query initial report via API
    resp = client.get("/api/v1/admin/validation-report", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "grouped_by_entity" in data
    assert "shows" in data["grouped_by_entity"]
    assert "episodes" in data["grouped_by_entity"]
    assert "seasons" in data["grouped_by_entity"]
    assert "artwork" in data["grouped_by_entity"]
    assert "other" in data["grouped_by_entity"]

def test_validation_service_published_show_without_section(client, auth_headers, db_session):
    show_resp = client.post("/api/v1/shows", json={
        "title": "Unassigned Section Show",
        "slug": "unassigned-sec",
        "section": "series",
        "status": "draft"
    }, headers=auth_headers)
    show_id = show_resp.json()["id"]

    show = db_session.query(Show).filter(Show.slug == "unassigned-sec").first()
    show.section = None
    show.status = "published"
    db_session.commit()

    report = ValidationService.audit_catalog(db_session)
    show_issues = [i for i in report.grouped_by_entity.shows if i.code == "SHOW_MISSING_SECTION"]
    assert len(show_issues) > 0
    assert show_issues[0].entity_id == str(show.id)
    assert "no homepage section assigned" in show_issues[0].problem
    assert "Assign a valid section" in show_issues[0].action
    assert report.can_publish is False
    assert report.blocking_count >= 1

def test_validation_service_published_episode_missing_duration_and_artwork(client, auth_headers, db_session):
    show_resp = client.post("/api/v1/shows", json={
        "title": "Issue Show",
        "slug": "issue-show",
        "section": "featured",
        "status": "published"
    }, headers=auth_headers)

    show = db_session.query(Show).filter(Show.slug == "issue-show").first()
    season = db_session.query(Season).filter(Season.show_id == show.id, Season.season_number == 1).first()

    # Ep 1: Missing duration
    ep_no_dur = Episode(
        custom_id="ep_bad_dur",
        show_id=show.id,
        season_id=season.id,
        episode_number=1,
        episode_title="Missing Duration Ep",
        duration_seconds=None,
        language="en",
        content_group="issue-cg-01",
        status="published",
        artwork_available=["thumbnail"]
    )

    # Ep 2: Missing artwork
    ep_no_art = Episode(
        custom_id="ep_bad_art",
        show_id=show.id,
        season_id=season.id,
        episode_number=2,
        episode_title="Missing Artwork Ep",
        duration_seconds=450,
        language="en",
        content_group="issue-cg-02",
        status="published",
        artwork_available=[]
    )

    db_session.add_all([ep_no_dur, ep_no_art])
    db_session.commit()

    report = ValidationService.audit_catalog(db_session)
    ep_issues = report.grouped_by_entity.episodes

    dur_issue = next((i for i in ep_issues if i.code == "EPISODE_MISSING_DURATION" and i.entity_id == "ep_bad_dur"), None)
    assert dur_issue is not None
    assert "no runtime duration" in dur_issue.problem
    assert "Add the episode duration" in dur_issue.action

    art_issue = next((i for i in ep_issues if i.code == "EPISODE_MISSING_ARTWORK" and i.entity_id == "ep_bad_art"), None)
    assert art_issue is not None
    assert "no artwork available" in art_issue.problem
    assert "Upload a 16:9 thumbnail" in art_issue.action

    assert report.can_publish is False

def test_validation_report_api_endpoint(client, auth_headers):
    resp = client.get("/api/v1/admin/validation-report", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "can_publish" in body
    assert "blocking_count" in body
    assert "grouped_by_entity" in body
    assert isinstance(body["grouped_by_entity"]["shows"], list)
    assert isinstance(body["grouped_by_entity"]["episodes"], list)
