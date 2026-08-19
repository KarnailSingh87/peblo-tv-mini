import os
import json
import pytest
from backend.app.models.entities import Show, Season, Episode, PublishRun
from backend.app.core.config import settings

@pytest.fixture
def admin_headers(client):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
def clean_catalogue_storage():
    storage_dir = os.path.abspath(settings.LOCAL_STORAGE_DIR)
    os.makedirs(storage_dir, exist_ok=True)
    live_filepath = os.path.join(storage_dir, "catalogue.json")
    if os.path.exists(live_filepath):
        try:
            os.remove(live_filepath)
        except Exception:
            pass
    yield
    if os.path.exists(live_filepath):
        try:
            os.remove(live_filepath)
        except Exception:
            pass

def _seed_valid_clean_show(db):
    show = Show(
        title="Magic Forest",
        slug="magic-forest",
        section="series",
        categories=["adventure", "nature"],
        status="published"
    )
    db.add(show)
    db.flush()

    s1 = Season(show_id=show.id, season_number=1, title="Season 1")
    db.add(s1)
    db.flush()

    ep1 = Episode(
        custom_id="ep_mf_01",
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        episode_title="Tree of Lights",
        duration_seconds=400,
        language="en",
        content_group="mf-s01e01",
        status="published",
        artwork_available=["thumbnail", "poster"]
    )
    db.add(ep1)
    db.commit()
    return show

# 1. Test Editor receives 403
def test_editor_receives_403_on_publish(client, auth_headers):
    # auth_headers is logged in as editor
    resp = client.post("/api/v1/admin/catalog/publish", headers=auth_headers)
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"]

    runs_resp = client.get("/api/v1/admin/catalog/publish-runs", headers=auth_headers)
    assert runs_resp.status_code == 403

# 2. Test Invalid content doesn't replace catalogue
def test_invalid_content_prevents_publish(client, admin_headers, db_session):
    # Create invalid published episode without duration and artwork
    show = Show(
        title="Invalid Show",
        slug="invalid-show",
        section="series",
        categories=["adventure"],
        status="published"
    )
    db_session.add(show)
    db_session.flush()

    s1 = Season(show_id=show.id, season_number=1, title="Season 1")
    db_session.add(s1)
    db_session.flush()

    bad_ep = Episode(
        custom_id="ep_bad_pub",
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        episode_title="Missing Stuff",
        duration_seconds=None,  # Blocker
        language="en",
        content_group="bad-cg",
        status="published",
        artwork_available=[]   # Blocker
    )
    db_session.add(bad_ep)
    db_session.commit()

    resp = client.post("/api/v1/admin/catalog/publish", headers=admin_headers)
    assert resp.status_code == 422
    data = resp.json()["detail"]
    assert "validation blockers" in data["error"]
    assert len(data["blockers"]) >= 2

    # Verify no live catalogue was generated
    cat_resp = client.get("/api/v1/catalog")
    assert cat_resp.status_code == 404

    # Verify failed PublishRun recorded
    runs = db_session.query(PublishRun).all()
    assert len(runs) == 1
    assert runs[0].status == "failed"

# 3. Test Successful Publish & 4. Catalogue Readable After Publish
def test_successful_publish_and_viewer_access(client, admin_headers, db_session):
    _seed_valid_clean_show(db_session)

    # Publish catalogue as admin
    pub_resp = client.post("/api/v1/admin/catalog/publish", headers=admin_headers)
    assert pub_resp.status_code == 200
    pub_data = pub_resp.json()
    assert pub_data["status"] == "success"
    assert pub_data["publish_run"]["status"] == "success"
    assert pub_data["publish_run"]["catalogue_version"] == 1
    assert pub_data["publish_run"]["show_count"] == 1
    assert pub_data["publish_run"]["episode_count"] == 1

    # Verify viewer endpoint reads the published catalogue
    cat_resp = client.get("/api/v1/catalog")
    assert cat_resp.status_code == 200
    catalog = cat_resp.json()
    assert catalog["version"] == 1
    assert catalog["total_shows"] == 1
    assert catalog["sections"][0]["shows"][0]["slug"] == "magic-forest"

# 5. Test Failed Publish leaves previous catalogue intact
def test_failed_publish_leaves_previous_catalogue_intact(client, admin_headers, db_session):
    # Step 1: Initial successful publish (version 1)
    show = _seed_valid_clean_show(db_session)
    pub1 = client.post("/api/v1/admin/catalog/publish", headers=admin_headers)
    assert pub1.status_code == 200

    # Verify version 1 is live
    v1_catalog = client.get("/api/v1/catalog").json()
    assert v1_catalog["version"] == 1

    # Step 2: Corrupt the catalog by inserting a broken published episode
    s1 = db_session.query(Season).filter(Season.show_id == show.id, Season.season_number == 1).first()
    broken_ep = Episode(
        custom_id="ep_broken_pub",
        show_id=show.id,
        season_id=s1.id,
        episode_number=2,
        episode_title="Broken Second Episode",
        duration_seconds=None,  # Blocker
        language="en",
        content_group="broken-cg",
        status="published",
        artwork_available=[]   # Blocker
    )
    db_session.add(broken_ep)
    db_session.commit()

    # Step 3: Attempt second publish -> MUST fail with 422
    pub2 = client.post("/api/v1/admin/catalog/publish", headers=admin_headers)
    assert pub2.status_code == 422

    # Step 4: Verify previous version 1 catalogue is STILL 100% available and uncorrupted
    v1_after_fail = client.get("/api/v1/catalog").json()
    assert v1_after_fail["version"] == 1
    assert v1_after_fail["total_shows"] == 1

# 6. Test Repeated publish behaves safely & increments version
def test_repeated_publish_idempotency_and_versioning(client, admin_headers, db_session):
    _seed_valid_clean_show(db_session)

    # Publish 1
    r1 = client.post("/api/v1/admin/catalog/publish", headers=admin_headers)
    assert r1.status_code == 200
    assert r1.json()["publish_run"]["catalogue_version"] == 1

    # Publish 2 (unchanged data)
    r2 = client.post("/api/v1/admin/catalog/publish", headers=admin_headers)
    assert r2.status_code == 200
    assert r2.json()["publish_run"]["catalogue_version"] == 2

    # Check history endpoint
    runs_resp = client.get("/api/v1/admin/catalog/publish-runs", headers=admin_headers)
    assert runs_resp.status_code == 200
    runs = runs_resp.json()
    assert len(runs) == 2
    assert runs[0]["catalogue_version"] == 2
    assert runs[1]["catalogue_version"] == 1
