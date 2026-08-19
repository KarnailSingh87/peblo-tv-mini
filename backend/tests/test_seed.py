import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.entities import Base, Show, Season, Episode, User
from backend.app.db.seed import run_seed

@pytest.fixture
def seed_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_seed_process_integrity_and_idempotency(seed_db):
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "seed_shows.json")),
        os.path.abspath("seed_shows.json"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed_shows.json"))
    ]
    json_path = next((c for c in candidates if os.path.exists(c)), None)
    assert json_path is not None, f"Seed data missing at {candidates}"

    # 1. First Seed Run
    report_1 = run_seed(seed_db, json_path=json_path)

    assert report_1["shows_created"] == 8
    assert report_1["total_records_in_json"] == 95
    assert report_1["episodes_created"] >= 94  # 94 unique (cg, lang) episodes (ep_9001 duplicate collision reported)

    # 2. Verify Shows Created
    shows = seed_db.query(Show).all()
    assert len(shows) == 8
    show_slugs = {s.slug for s in shows}
    assert "motis-many-lives" in show_slugs
    assert "rhyme-rangers" in show_slugs
    assert "peblo-songs" in show_slugs

    # 3. Verify Season 0 Preservation
    s0_seasons = seed_db.query(Season).filter(Season.season_number == 0).all()
    assert len(s0_seasons) == 2  # Moti's Many Lives and Tiny Tales by Banyan Dadi
    for s0 in s0_seasons:
        assert s0.season_number == 0
        assert s0.title == "Trailers"
        assert len(s0.episodes) == 1
        assert s0.episodes[0].episode_title == "Trailer"

    # 4. Verify Content Group and Multilingual Variant Ingestion
    moti_s1e1_eps = seed_db.query(Episode).filter(Episode.content_group == "motis-many-lives-s01e01").all()
    assert len(moti_s1e1_eps) == 2
    langs = {e.language for e in moti_s1e1_eps}
    assert langs == {"en", "hi"}

    # 5. Verify Validation Problems are Reported Without Silent Fixing
    # Issue A: Missing artwork on ep_0036
    art_issues = [i for i in report_1["validation_issues_found"] if i["type"] == "EPISODE_MISSING_ARTWORK"]
    assert any(i["custom_id"] == "ep_0036" for i in art_issues)

    # Issue B: Duplicate (content_group, language) on ep_9001
    dup_conflicts = [c for c in report_1["duplicate_conflicts"] if c["custom_id"] == "ep_9001"]
    assert len(dup_conflicts) > 0
    assert dup_conflicts[0]["content_group"] == "motis-many-lives-s01e02"
    assert dup_conflicts[0]["language"] == "hi"

    # Issue C: Show without section on Rhyme Rangers
    sec_issues = [i for i in report_1["validation_issues_found"] if i["type"] == "SHOW_MISSING_SECTION"]
    assert any(i["slug"] == "rhyme-rangers" for i in sec_issues)

    # 6. Verify Idempotency on Second Run
    report_2 = run_seed(seed_db, json_path=json_path)
    assert report_2["shows_created"] == 0
    assert report_2["seasons_created"] == 0
    assert report_2["episodes_created"] == 0
    assert report_2["shows_updated"] == 8
    assert report_2["episodes_updated"] == report_1["episodes_created"]

    # Verify final counts in database remained exactly identical
    assert seed_db.query(Show).count() == 8
    assert seed_db.query(Season).count() == 10
    assert seed_db.query(Episode).count() == report_1["episodes_created"]
