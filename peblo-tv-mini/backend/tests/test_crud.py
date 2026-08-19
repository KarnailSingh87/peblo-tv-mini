import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.main import app
from backend.app.db.session import get_db
from backend.app.models.entities import Base, User, Show, Season, Episode
from backend.app.core.security import get_password_hash

# Uses shared fixtures from conftest.py

# --- 1. SHOW VALIDATION & CRUD TESTS ---

def test_create_show_valid(client, auth_headers):
    payload = {
        "title": "Moti's Many Lives",
        "slug": "motis-many-lives",
        "section": "featured",
        "categories": ["adventure", "india"],
        "synopsis": "Moti travels across India.",
        "status": "published"
    }
    resp = client.post("/api/v1/shows", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Moti's Many Lives"
    assert data["slug"] == "motis-many-lives"
    assert len(data["seasons"]) == 2  # Season 0 (Trailers) and Season 1
    assert data["seasons"][0]["season_number"] == 0
    assert data["seasons"][0]["title"] == "Trailers"
    assert data["seasons"][1]["season_number"] == 1

def test_create_show_duplicate_slug_rejected(client, auth_headers):
    payload = {
        "title": "Show A",
        "slug": "unique-slug",
        "section": "series",
        "status": "draft"
    }
    resp1 = client.post("/api/v1/shows", json=payload, headers=auth_headers)
    assert resp1.status_code == 201

    # Attempt second show with exact same slug
    resp2 = client.post("/api/v1/shows", json=payload, headers=auth_headers)
    assert resp2.status_code == 400
    assert "already in use" in resp2.json()["detail"]

def test_create_show_invalid_section_rejected(client, auth_headers):
    payload = {
        "title": "Show With Bad Section",
        "slug": "bad-section",
        "section": "invalid_section_name",
        "status": "draft"
    }
    resp = client.post("/api/v1/shows", json=payload, headers=auth_headers)
    assert resp.status_code == 422

def test_create_show_invalid_category_rejected(client, auth_headers):
    payload = {
        "title": "Show With Bad Category",
        "slug": "bad-category",
        "section": "series",
        "categories": ["adventure", "invalid_category_tag"],
        "status": "draft"
    }
    resp = client.post("/api/v1/shows", json=payload, headers=auth_headers)
    assert resp.status_code == 422

def test_create_published_show_without_section_rejected(client, auth_headers):
    payload = {
        "title": "Published Show No Section",
        "slug": "no-section-pub",
        "section": None,
        "status": "published"
    }
    resp = client.post("/api/v1/shows", json=payload, headers=auth_headers)
    assert resp.status_code == 422
    assert "must be assigned to a section" in resp.json()["detail"]

def test_show_pagination_and_search(client, auth_headers):
    for i in range(5):
        client.post("/api/v1/shows", json={
            "title": f"Story Time {i}",
            "slug": f"story-time-{i}",
            "section": "series",
            "categories": ["stories"],
            "status": "published"
        }, headers=auth_headers)

    # Page 1, Page size 2
    resp = client.get("/api/v1/shows?page=1&page_size=2", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["total_pages"] == 3

    # Search filter
    search_resp = client.get("/api/v1/shows?search=Story Time 3", headers=auth_headers)
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1
    assert search_resp.json()["items"][0]["slug"] == "story-time-3"

def test_delete_show_cascade(client, auth_headers):
    create_resp = client.post("/api/v1/shows", json={
        "title": "Show To Delete",
        "slug": "show-delete",
        "section": "songs",
        "status": "draft"
    }, headers=auth_headers)
    show_id = create_resp.json()["id"]

    # Delete show
    del_resp = client.delete(f"/api/v1/shows/{show_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # Verify not found
    get_resp = client.get(f"/api/v1/shows/{show_id}", headers=auth_headers)
    assert get_resp.status_code == 404

# --- 2. SEASONS ENDPOINTS TESTS ---

def test_show_seasons_endpoints(client, auth_headers):
    create_resp = client.post("/api/v1/shows", json={
        "title": "Seasons Show",
        "slug": "seasons-show",
        "section": "series",
        "status": "draft"
    }, headers=auth_headers)
    show_id = create_resp.json()["id"]

    # List seasons
    seasons_resp = client.get(f"/api/v1/shows/{show_id}/seasons", headers=auth_headers)
    assert seasons_resp.status_code == 200
    assert len(seasons_resp.json()) == 2  # Season 0 and Season 1

    # Create Season 2
    create_s2 = client.post(f"/api/v1/shows/{show_id}/seasons", json={"season_number": 2, "title": "Season Two"}, headers=auth_headers)
    assert create_s2.status_code == 201
    assert create_s2.json()["season_number"] == 2

    # Attempt duplicate season number
    dup_s2 = client.post(f"/api/v1/shows/{show_id}/seasons", json={"season_number": 2}, headers=auth_headers)
    assert dup_s2.status_code == 400

# --- 3. EPISODE VALIDATION & CRUD TESTS ---

def test_create_and_validate_episodes(client, auth_headers):
    # 1. Create show and get Season 1 ID
    show_resp = client.post("/api/v1/shows", json={
        "title": "Episode Parent Show",
        "slug": "ep-show",
        "section": "series",
        "status": "draft"
    }, headers=auth_headers)
    season_1_id = show_resp.json()["seasons"][1]["id"]

    # 2. Create valid English episode
    ep1_payload = {
        "custom_id": "ep_0001",
        "episode_number": 1,
        "episode_title": "The Lost Kite",
        "duration_seconds": 500,
        "language": "en",
        "content_group": "kite-episode-01",
        "status": "published",
        "artwork_available": ["thumbnail", "poster"]
    }
    ep1_resp = client.post(f"/api/v1/seasons/{season_1_id}/episodes", json=ep1_payload, headers=auth_headers)
    assert ep1_resp.status_code == 201
    assert ep1_resp.json()["custom_id"] == "ep_0001"

    # 3. Create valid Hindi language variant in same content group
    ep2_payload = {
        "custom_id": "ep_0002",
        "episode_number": 1,
        "episode_title": "Patang Kho Gayi",
        "duration_seconds": 510,
        "language": "hi",
        "content_group": "kite-episode-01",
        "status": "published",
        "artwork_available": ["thumbnail", "poster"]
    }
    ep2_resp = client.post(f"/api/v1/seasons/{season_1_id}/episodes", json=ep2_payload, headers=auth_headers)
    assert ep2_resp.status_code == 201
    assert ep2_resp.json()["language"] == "hi"

    # 4. Attempt duplicate (content_group, language) -> MUST reject (HTTP 400)
    ep_dup_payload = {
        "custom_id": "ep_9999",
        "episode_number": 1,
        "episode_title": "The Lost Kite Duplicate",
        "duration_seconds": 500,
        "language": "en",
        "content_group": "kite-episode-01",
        "status": "draft"
    }
    dup_resp = client.post(f"/api/v1/seasons/{season_1_id}/episodes", json=ep_dup_payload, headers=auth_headers)
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]

    # 5. Invalid language code (e.g. 'fr') -> MUST reject (HTTP 422)
    bad_lang_payload = {
        "episode_title": "French Ep",
        "language": "fr",
        "content_group": "french-ep-01"
    }
    bad_lang_resp = client.post(f"/api/v1/seasons/{season_1_id}/episodes", json=bad_lang_payload, headers=auth_headers)
    assert bad_lang_resp.status_code == 422

    # 6. Published episode with missing duration -> MUST reject (HTTP 422)
    bad_dur_payload = {
        "episode_title": "No Duration Pub",
        "language": "en",
        "content_group": "no-dur-ep",
        "status": "published",
        "duration_seconds": None,
        "artwork_available": ["thumbnail"]
    }
    bad_dur_resp = client.post(f"/api/v1/seasons/{season_1_id}/episodes", json=bad_dur_payload, headers=auth_headers)
    assert bad_dur_resp.status_code == 422
    assert "valid positive duration" in bad_dur_resp.json()["detail"]

    # 7. Published episode with missing artwork -> MUST reject (HTTP 422)
    bad_art_payload = {
        "episode_title": "No Art Pub",
        "language": "en",
        "content_group": "no-art-ep",
        "status": "published",
        "duration_seconds": 300,
        "artwork_available": []
    }
    bad_art_resp = client.post(f"/api/v1/seasons/{season_1_id}/episodes", json=bad_art_payload, headers=auth_headers)
    assert bad_art_resp.status_code == 422
    assert "must have artwork available" in bad_art_resp.json()["detail"]

    # 8. Episode lookup by custom_id ('ep_0001')
    lookup_resp = client.get("/api/v1/episodes/ep_0001", headers=auth_headers)
    assert lookup_resp.status_code == 200
    assert lookup_resp.json()["episode_title"] == "The Lost Kite"

    # 9. Episode update
    update_resp = client.put("/api/v1/episodes/ep_0001", json={"episode_title": "The Lost Kite (Remastered)"}, headers=auth_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["episode_title"] == "The Lost Kite (Remastered)"

    # 10. Episode deletion
    del_ep_resp = client.delete("/api/v1/episodes/ep_0001", headers=auth_headers)
    assert del_ep_resp.status_code == 204
    assert client.get("/api/v1/episodes/ep_0001", headers=auth_headers).status_code == 404
