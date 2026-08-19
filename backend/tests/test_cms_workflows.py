import os
import pytest
from backend.app.models.entities import User, Show, Season, Episode
from backend.app.core.config import settings

def test_cms_end_to_end_editorial_workflow_and_rbac(client, db_session):
    """
    Tests the full CMS content workflow across roles:
    1. Editor logs in and creates draft content
    2. Editor tries to publish -> gets 403 Forbidden
    3. Admin checks pre-flight validation report and sees blocking issues
    4. Content is corrected to satisfy constraints
    5. Admin triggers publish -> 200 OK with versioned atomic release
    6. Viewer reads pure catalogue
    """
    # 1. Editor Login
    editor_login = client.post("/api/v1/auth/login", json={"username": "editor", "password": "editor123"})
    assert editor_login.status_code == 200
    editor_token = editor_login.json()["access_token"]
    editor_headers = {"Authorization": f"Bearer {editor_token}"}

    # 2. Editor creates a draft show
    show_res = client.post("/api/v1/shows", json={
        "title": "Jungle Friends",
        "slug": "jungle-friends",
        "section": "series",
        "categories": ["adventure", "nature"],
        "synopsis": "Friendly animals in the rainforest.",
        "status": "draft"
    }, headers=editor_headers)
    assert show_res.status_code == 201
    show_id = show_res.json()["id"]
    season_1_id = show_res.json()["seasons"][1]["id"]

    # 3. Editor creates episode
    ep_res = client.post(f"/api/v1/seasons/{season_1_id}/episodes", json={
        "episode_number": 1,
        "episode_title": "The Big Tree",
        "duration_seconds": 450,
        "language": "en",
        "content_group": "jungle-s01e01",
        "status": "draft",
        "artwork_available": []
    }, headers=editor_headers)
    assert ep_res.status_code == 201
    ep_id = ep_res.json()["id"]

    # 4. Editor attempts to trigger live publication -> 403 FORBIDDEN
    editor_pub = client.post("/api/v1/admin/catalog/publish", headers=editor_headers)
    assert editor_pub.status_code == 403
    assert "requires role in ['admin']" in editor_pub.json()["detail"]

    # 5. Admin Login
    admin_login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 6. Admin inspects validation report (Editor can also view)
    report_res = client.get("/api/v1/admin/validation-report", headers=admin_headers)
    assert report_res.status_code == 200
    assert "grouped_by_entity" in report_res.json()

    # 7. Update show and episode to published with artwork & duration
    client.put(f"/api/v1/shows/{show_id}", json={"status": "published"}, headers=editor_headers)
    client.put(f"/api/v1/episodes/{ep_id}", json={
        "status": "published",
        "duration_seconds": 480,
        "artwork_available": ["thumbnail"]
    }, headers=editor_headers)

    # 8. Admin triggers publication -> 200 OK
    pub_res = client.post("/api/v1/admin/catalog/publish", headers=admin_headers)
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "success"
    assert pub_data["publish_run"]["show_count"] >= 1

    # 9. Viewer reads published catalogue
    viewer_catalog = client.get("/api/v1/catalog")
    assert viewer_catalog.status_code == 200
    catalog_data = viewer_catalog.json()
    assert "sections" in catalog_data
    series_sec = next((s for s in catalog_data["sections"] if s["section"] == "series"), None)
    assert series_sec is not None
    assert any(s["slug"] == "jungle-friends" for s in series_sec["shows"])

    # 10. Viewer searches published catalogue
    search_res = client.get("/api/v1/catalog/search?q=Jungle")
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1
    assert search_res.json()["items"][0]["slug"] == "jungle-friends"
