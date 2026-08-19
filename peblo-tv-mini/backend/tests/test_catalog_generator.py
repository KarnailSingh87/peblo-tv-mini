import pytest
from backend.app.models.entities import Show, Season, Episode, Artwork
from backend.app.services.catalog_generator import CatalogueGenerator, CatalogueGenerationError

def test_unpublished_content_excluded(db_session):
    # 1. Create a published show and a draft show
    pub_show = Show(
        title="Published Adventures",
        slug="pub-adv",
        section="series",
        categories=["adventure"],
        status="published"
    )
    draft_show = Show(
        title="Draft Stories",
        slug="draft-stories",
        section="series",
        categories=["stories"],
        status="draft"
    )
    db_session.add_all([pub_show, draft_show])
    db_session.flush()

    s1 = Season(show_id=pub_show.id, season_number=1, title="Season 1")
    s_draft = Season(show_id=draft_show.id, season_number=1, title="Season 1")
    db_session.add_all([s1, s_draft])
    db_session.flush()

    # Create 1 published episode and 1 draft episode in the published show
    ep_pub = Episode(
        custom_id="ep_pub",
        show_id=pub_show.id,
        season_id=s1.id,
        episode_number=1,
        episode_title="Published Episode",
        duration_seconds=300,
        language="en",
        content_group="pub-cg-01",
        status="published",
        artwork_available=["thumbnail"]
    )
    ep_draft = Episode(
        custom_id="ep_draft",
        show_id=pub_show.id,
        season_id=s1.id,
        episode_number=2,
        episode_title="Draft Episode",
        duration_seconds=300,
        language="en",
        content_group="draft-cg-02",
        status="draft",
        artwork_available=["thumbnail"]
    )
    db_session.add_all([ep_pub, ep_draft])
    db_session.commit()

    # Generate catalogue without validation blocking
    catalog = CatalogueGenerator.generate_catalogue(db_session, check_validation=False)

    # Verify draft show is excluded
    all_show_slugs = [s.slug for sec in catalog.sections for s in sec.shows]
    assert "pub-adv" in all_show_slugs
    assert "draft-stories" not in all_show_slugs

    # Verify draft episode is excluded from published show
    pub_show_entry = next(s for sec in catalog.sections for s in sec.shows if s.slug == "pub-adv")
    assert len(pub_show_entry.seasons) == 1
    assert len(pub_show_entry.seasons[0].episodes) == 1
    assert pub_show_entry.seasons[0].episodes[0].content_group == "pub-cg-01"

def test_content_group_multilingual_collapsing(db_session):
    show = Show(
        title="Moti's Multilingual Lives",
        slug="moti-multi",
        section="featured",
        categories=["india", "friendship"],
        status="published"
    )
    db_session.add(show)
    db_session.flush()

    s1 = Season(show_id=show.id, season_number=1, title="Season 1")
    db_session.add(s1)
    db_session.flush()

    # Add English and Hindi variants of same episode (content_group: 'moti-s01e01')
    ep_en = Episode(
        custom_id="ep_0001",
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        episode_title="The Lost Kite",
        duration_seconds=510,
        language="en",
        content_group="moti-s01e01",
        status="published",
        artwork_available=["thumbnail", "poster"]
    )
    ep_hi = Episode(
        custom_id="ep_0002",
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        episode_title="Patang Kho Gayi",
        duration_seconds=520,
        language="hi",
        content_group="moti-s01e01",
        status="published",
        artwork_available=["thumbnail", "poster"]
    )
    db_session.add_all([ep_en, ep_hi])
    db_session.commit()

    catalog = CatalogueGenerator.generate_catalogue(db_session, check_validation=False)
    show_entry = catalog.sections[0].shows[0]

    # Must collapse into 1 episode entry
    assert len(show_entry.seasons[0].episodes) == 1
    cat_ep = show_entry.seasons[0].episodes[0]

    assert cat_ep.content_group == "moti-s01e01"
    assert cat_ep.languages == ["en", "hi"]
    assert len(cat_ep.variants) == 2
    assert {v.language for v in cat_ep.variants} == {"en", "hi"}
    assert {v.episode_title for v in cat_ep.variants} == {"The Lost Kite", "Patang Kho Gayi"}

def test_season_0_trailer_isolation(db_session):
    show = Show(
        title="Show With Trailer",
        slug="show-trailer",
        section="series",
        categories=["nature"],
        status="published"
    )
    db_session.add(show)
    db_session.flush()

    s0 = Season(show_id=show.id, season_number=0, title="Trailers")
    s1 = Season(show_id=show.id, season_number=1, title="Season 1")
    db_session.add_all([s0, s1])
    db_session.flush()

    trailer_ep = Episode(
        custom_id="ep_trailer",
        show_id=show.id,
        season_id=s0.id,
        episode_number=1,
        episode_title="Official Series Trailer",
        duration_seconds=60,
        language="en",
        content_group="trailer-cg",
        status="published",
        artwork_available=["thumbnail"]
    )
    regular_ep = Episode(
        custom_id="ep_s1e1",
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        episode_title="First Real Episode",
        duration_seconds=600,
        language="en",
        content_group="s01e01-cg",
        status="published",
        artwork_available=["thumbnail"]
    )
    db_session.add_all([trailer_ep, regular_ep])
    db_session.commit()

    catalog = CatalogueGenerator.generate_catalogue(db_session, check_validation=False)
    show_entry = next(s for sec in catalog.sections for s in sec.shows if s.slug == "show-trailer")

    # Season 0 MUST NOT appear in seasons list
    season_numbers = [s.season_number for s in show_entry.seasons]
    assert 0 not in season_numbers
    assert season_numbers == [1]

    # Season 0 MUST appear under trailers list
    assert len(show_entry.trailers) == 1
    assert show_entry.trailers[0].content_group == "trailer-cg"
    assert show_entry.trailers[0].title == "Official Series Trailer"

def test_deterministic_ordering(db_session):
    # Create shows in reverse order across sections
    show_b = Show(title="Bebra", slug="bebra", section="songs", categories=["music"], status="published")
    show_a = Show(title="Alpha", slug="alpha", section="songs", categories=["music"], status="published")
    show_feat = Show(title="Featured Show", slug="feat-show", section="featured", categories=["learning"], status="published")
    db_session.add_all([show_b, show_a, show_feat])
    db_session.flush()

    for s in [show_b, show_a, show_feat]:
        s1 = Season(show_id=s.id, season_number=1, title="Season 1")
        db_session.add(s1)
        db_session.flush()
        ep = Episode(
            custom_id=f"ep_{s.slug}",
            show_id=s.id,
            season_id=s1.id,
            episode_number=1,
            episode_title=f"{s.title} Ep",
            duration_seconds=300,
            language="en",
            content_group=f"{s.slug}-cg",
            status="published",
            artwork_available=["thumbnail"]
        )
        db_session.add(ep)

    db_session.commit()

    catalog = CatalogueGenerator.generate_catalogue(db_session, check_validation=False)

    # 1. Sections order strictly matches ALLOWED_SECTIONS ("featured", then "songs")
    section_names = [sec.section for sec in catalog.sections]
    assert section_names == ["featured", "songs"]

    # 2. Shows inside "songs" section are deterministically ordered by title ("Alpha", then "Bebra")
    songs_sec = next(sec for sec in catalog.sections if sec.section == "songs")
    show_titles = [s.title for s in songs_sec.shows]
    assert show_titles == ["Alpha", "Bebra"]

def test_invalid_content_prevents_publish_candidate(db_session):
    # Create a published show with a published episode that lacks duration and artwork (blocking issues)
    show = Show(
        title="Broken Show",
        slug="broken-show",
        section="series",
        categories=["adventure"],
        status="published"
    )
    db_session.add(show)
    db_session.flush()

    s1 = Season(show_id=show.id, season_number=1, title="Season 1")
    db_session.add(s1)
    db_session.flush()

    broken_ep = Episode(
        custom_id="broken_ep",
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        episode_title="Broken Ep",
        duration_seconds=None,  # Missing duration blocker
        language="en",
        content_group="broken-cg",
        status="published",
        artwork_available=[]   # Missing artwork blocker
    )
    db_session.add(broken_ep)
    db_session.commit()

    # Attempting to generate catalog with validation check MUST raise CatalogueGenerationError
    with pytest.raises(CatalogueGenerationError) as exc_info:
        CatalogueGenerator.generate_catalogue(db_session, check_validation=True)

    assert "Catalogue generation blocked" in str(exc_info.value)
    assert len(exc_info.value.blockers) >= 2
    assert any("EPISODE_MISSING_DURATION" in b for b in exc_info.value.blockers)
    assert any("EPISODE_MISSING_ARTWORK" in b for b in exc_info.value.blockers)
