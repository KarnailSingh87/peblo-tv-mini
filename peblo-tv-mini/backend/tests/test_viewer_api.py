import os
import json
import pytest
from backend.app.models.entities import Show, Season, Episode, User
from backend.app.services.publisher import CataloguePublisher
from backend.app.core.config import settings

@pytest.fixture(autouse=True)
def setup_test_catalogue(db_session):
    # 1. Clean previous catalogue.json
    storage_dir = os.path.abspath(settings.LOCAL_STORAGE_DIR)
    os.makedirs(storage_dir, exist_ok=True)
    live_filepath = os.path.join(storage_dir, "catalogue.json")
    if os.path.exists(live_filepath):
        try:
            os.remove(live_filepath)
        except Exception:
            pass

    # 2. Seed 3 distinct published shows with episodes and language variants
    show1 = Show(
        title="Moti's Grand Adventure",
        slug="motis-grand-adventure",
        section="featured",
        categories=["adventure", "india", "nature"],
        synopsis="A friendly dog named Moti explores historical cities of India.",
        status="published"
    )
    show2 = Show(
        title="Curious Cubs Math",
        slug="curious-cubs-math",
        section="series",
        categories=["maths", "learning", "science"],
        synopsis="Bear cubs learn to solve everyday math puzzles.",
        status="published"
    )
    show3 = Show(
        title="Lullaby Rhymes",
        slug="lullaby-rhymes",
        section="songs",
        categories=["music", "singalong"],
        synopsis="Calming bedtime nursery rhymes for toddlers.",
        status="published"
    )
    db_session.add_all([show1, show2, show3])
    db_session.flush()

    # Show 1 Seasons & Episodes (multilingual English + Hindi)
    s1_s0 = Season(show_id=show1.id, season_number=0, title="Trailers")
    s1_s1 = Season(show_id=show1.id, season_number=1, title="Season 1")
    db_session.add_all([s1_s0, s1_s1])
    db_session.flush()

    ep1_tr = Episode(
        custom_id="ep_moti_tr",
        show_id=show1.id,
        season_id=s1_s0.id,
        episode_number=1,
        episode_title="Official Moti Trailer",
        duration_seconds=90,
        language="en",
        content_group="moti-tr-01",
        status="published",
        artwork_available=["thumbnail"]
    )
    ep1_en = Episode(
        custom_id="ep_moti_01",
        show_id=show1.id,
        season_id=s1_s1.id,
        episode_number=1,
        episode_title="The Flying Kite",
        duration_seconds=500,
        language="en",
        content_group="moti-s01e01",
        status="published",
        artwork_available=["thumbnail"]
    )
    ep1_hi = Episode(
        custom_id="ep_moti_02",
        show_id=show1.id,
        season_id=s1_s1.id,
        episode_number=1,
        episode_title="Udti Patang",
        duration_seconds=490,
        language="hi",
        content_group="moti-s01e01",
        status="published",
        artwork_available=["thumbnail"]
    )

    # Show 2 Episodes (English only)
    s2_s1 = Season(show_id=show2.id, season_number=1, title="Season 1")
    db_session.add(s2_s1)
    db_session.flush()
    ep2_en = Episode(
        custom_id="ep_cubs_01",
        show_id=show2.id,
        season_id=s2_s1.id,
        episode_number=1,
        episode_title="Counting Berries",
        duration_seconds=420,
        language="en",
        content_group="cubs-s01e01",
        status="published",
        artwork_available=["thumbnail"]
    )

    # Show 3 Episodes (English + Hindi)
    s3_s1 = Season(show_id=show3.id, season_number=1, title="Season 1")
    db_session.add(s3_s1)
    db_session.flush()
    ep3_en = Episode(
        custom_id="ep_rhymes_01",
        show_id=show3.id,
        season_id=s3_s1.id,
        episode_number=1,
        episode_title="Twinkle Star Melodies",
        duration_seconds=210,
        language="en",
        content_group="rhymes-s01e01",
        status="published",
        artwork_available=["thumbnail"]
    )
    ep3_hi = Episode(
        custom_id="ep_rhymes_02",
        show_id=show3.id,
        season_id=s3_s1.id,
        episode_number=1,
        episode_title="Chanda Mama Lori",
        duration_seconds=220,
        language="hi",
        content_group="rhymes-s01e01",
        status="published",
        artwork_available=["thumbnail"]
    )

    db_session.add_all([ep1_tr, ep1_en, ep1_hi, ep2_en, ep3_en, ep3_hi])
    db_session.commit()

    # Publish the catalogue
    admin_user = db_session.query(User).filter(User.username == "admin").first()
    CataloguePublisher.publish(db_session, admin_user)

    yield

    if os.path.exists(live_filepath):
        try:
            os.remove(live_filepath)
        except Exception:
            pass

# --- TEST CASES ---

def test_get_published_catalogue(client):
    resp = client.get("/api/v1/catalog")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] >= 1
    assert data["total_shows"] == 3
    assert len(data["sections"]) == 3  # featured, series, songs

def test_search_by_show_title(client):
    # Match "Moti"
    resp = client.get("/api/v1/catalog/search?q=Moti")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "motis-grand-adventure"

def test_search_by_episode_title(client):
    # Match "Kite" (episode title in Moti's show)
    resp = client.get("/api/v1/catalog/search?q=Kite")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "motis-grand-adventure"
    assert "The Flying Kite" in data["items"][0]["matched_episodes"]

    # Match "Patang" (Hindi episode variant)
    resp_hi = client.get("/api/v1/catalog/search?q=Patang")
    assert resp_hi.status_code == 200
    assert resp_hi.json()["total"] == 1
    assert "Udti Patang" in resp_hi.json()["items"][0]["matched_episodes"]

def test_search_by_category(client):
    # Search for "india" (present in Show 1)
    resp = client.get("/api/v1/catalog/search?q=india")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "motis-grand-adventure"

def test_category_filter(client):
    resp = client.get("/api/v1/catalog/search?category=music")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "lullaby-rhymes"

def test_language_filter(client):
    # Filter by Hindi ("hi"): Show 1 and Show 3 support Hindi
    resp = client.get("/api/v1/catalog/search?language=hi")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    slugs = {item["slug"] for item in data["items"]}
    assert slugs == {"motis-grand-adventure", "lullaby-rhymes"}

def test_section_filter(client):
    # Filter by section "series" -> Show 2
    resp = client.get("/api/v1/catalog/search?section=series")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "curious-cubs-math"

def test_composed_filters(client):
    # Compose q="Moti" + language="hi" + section="featured"
    resp = client.get("/api/v1/catalog/search?q=Moti&language=hi&section=featured")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "motis-grand-adventure"

    # Conflicting composition: q="Moti" + section="songs" -> 0 matches
    resp_empty = client.get("/api/v1/catalog/search?q=Moti&section=songs")
    assert resp_empty.status_code == 200
    assert resp_empty.json()["total"] == 0
    assert resp_empty.json()["items"] == []

def test_empty_search_results(client):
    resp = client.get("/api/v1/catalog/search?q=nonexistentqueryxyz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["total_pages"] == 1
    assert data["items"] == []

def test_search_pagination(client):
    # Fetch all shows with page_size=1
    resp_p1 = client.get("/api/v1/catalog/search?page=1&page_size=1")
    assert resp_p1.status_code == 200
    data1 = resp_p1.json()
    assert data1["total"] == 3
    assert data1["total_pages"] == 3
    assert len(data1["items"]) == 1

    resp_p2 = client.get("/api/v1/catalog/search?page=2&page_size=1")
    assert resp_p2.status_code == 200
    data2 = resp_p2.json()
    assert len(data2["items"]) == 1
    assert data2["items"][0]["id"] != data1["items"][0]["id"]
