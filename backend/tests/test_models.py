import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.entities import Base, User, Show, Season, Episode, Artwork, PublishRun

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_models_relationships_and_constraints(db_session):
    # 1. Create Show
    show = Show(
        title="Moti's Many Lives",
        slug="motis-many-lives",
        section="featured",
        categories=["adventure", "india"],
        synopsis="Moti the dog travels India.",
        status="published"
    )
    db_session.add(show)
    db_session.commit()
    db_session.refresh(show)

    assert isinstance(show.id, uuid.UUID)
    assert show.title == "Moti's Many Lives"

    # 2. Create Season (Season 0 Trailer & Season 1)
    s0 = Season(show_id=show.id, season_number=0, title="Trailers")
    s1 = Season(show_id=show.id, season_number=1, title="Season 1")
    db_session.add_all([s0, s1])
    db_session.commit()

    # 3. Create Multilingual Episodes in same content group
    ep_en = Episode(
        custom_id="ep_0001",
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        episode_title="The Lost Kite",
        duration_seconds=510,
        language="en",
        content_group="motis-many-lives-s01e01",
        status="published",
        artwork_available=["poster", "banner", "thumbnail"]
    )
    ep_hi = Episode(
        custom_id="ep_0002",
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        episode_title="Patang Kho Gayi",
        duration_seconds=520,
        language="hi",
        content_group="motis-many-lives-s01e01",
        status="published",
        artwork_available=["poster", "banner", "thumbnail"]
    )
    db_session.add_all([ep_en, ep_hi])
    db_session.commit()

    # Verify relationships
    assert len(show.seasons) == 2
    assert len(s1.episodes) == 2
    assert ep_en.season.season_number == 1
    assert ep_en.show.title == "Moti's Many Lives"

    # 4. Create Artwork
    art = Artwork(
        entity_type="show",
        show_id=show.id,
        episode_id=None,
        artwork_type="banner",
        file_path="uploads/show/banner.jpg",
        url="/api/v1/storage/uploads/show/banner.jpg",
        width=1280,
        height=720,
        file_size_bytes=150000,
        mime_type="image/jpeg"
    )
    db_session.add(art)
    db_session.commit()
    db_session.refresh(show)

    assert len(show.artwork) == 1
    assert show.artwork[0].artwork_type == "banner"

    # 5. Create Publish Run
    run = PublishRun(
        version=1,
        triggered_by="admin",
        status="success",
        show_count=1,
        episode_count=1,
        file_path="catalogue/catalogue_v1.json",
        metadata_json={"sections_count": 1}
    )
    db_session.add(run)
    db_session.commit()

    assert isinstance(run.id, uuid.UUID)
    assert run.version == 1
