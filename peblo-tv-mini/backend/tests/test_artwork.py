import io
import pytest
from PIL import Image
from backend.app.services.artwork_service import ArtworkService

def _create_test_image(width: int, height: int, format: str = "JPEG", quality: int = 80, size_target_kb: int = None) -> bytes:
    """Helper creating in-memory image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    img.save(buf, format=format, quality=quality)
    data = buf.getvalue()

    if size_target_kb:
        # Pad with dummy bytes at end if needed to exceed file size threshold
        needed = (size_target_kb * 1024) - len(data)
        if needed > 0:
            data += b"\x00" * (needed + 512)

    return data

# --- 1. POSTER VALIDATION TESTS ---

def test_valid_poster():
    # 600x900px is exact 2:3 vertical aspect ratio (~0.667)
    poster_bytes = _create_test_image(600, 900, format="JPEG")
    res = ArtworkService.validate_artwork(poster_bytes, "poster", "poster.jpg")
    assert res.is_valid is True
    assert res.width == 600
    assert res.height == 900
    assert len(res.errors) == 0

def test_wrong_poster_ratio():
    # 900x600px is horizontal (1.5 aspect ratio) -> MUST reject
    landscape_bytes = _create_test_image(900, 600, format="JPEG")
    res = ArtworkService.validate_artwork(landscape_bytes, "poster", "landscape_poster.jpg")
    assert res.is_valid is False
    assert any("Poster must be vertical" in err for err in res.errors)

    # 600x600px square -> MUST reject
    square_bytes = _create_test_image(600, 600, format="JPEG")
    res_sq = ArtworkService.validate_artwork(square_bytes, "poster", "square.jpg")
    assert res_sq.is_valid is False
    assert any("aspect ratio" in err.lower() for err in res_sq.errors)

# --- 2. BANNER VALIDATION TESTS ---

def test_valid_banner():
    # 1280x720px is exact 16:9 widescreen aspect ratio (~1.778)
    banner_bytes = _create_test_image(1280, 720, format="JPEG")
    res = ArtworkService.validate_artwork(banner_bytes, "banner", "banner.jpg")
    assert res.is_valid is True
    assert res.width == 1280
    assert res.height == 720
    assert len(res.errors) == 0

def test_oversized_banner():
    # Exceeds 200 KB limit (e.g. 250 KB)
    oversized_bytes = _create_test_image(1280, 720, format="JPEG", size_target_kb=250)
    res = ArtworkService.validate_artwork(oversized_bytes, "banner", "big_banner.jpg")
    assert res.is_valid is False
    assert any("exceeds the maximum allowed limit of 200 KB" in err for err in res.errors)

# --- 3. THUMBNAIL VALIDATION TESTS ---

def test_valid_thumbnail():
    # 640x360px is exact 16:9 aspect ratio
    thumb_bytes = _create_test_image(640, 360, format="JPEG")
    res = ArtworkService.validate_artwork(thumb_bytes, "thumbnail", "thumb.jpg")
    assert res.is_valid is True
    assert res.width == 640
    assert res.height == 360

def test_tiny_thumbnail():
    # 200x112px is too small (below minimum dimensions 480x270)
    tiny_bytes = _create_test_image(200, 112, format="JPEG")
    res = ArtworkService.validate_artwork(tiny_bytes, "thumbnail", "tiny.jpg")
    assert res.is_valid is False
    assert any("too small" in err for err in res.errors)

# --- 4. UPLOAD ENDPOINT INTEGRATION TEST ---

def test_artwork_upload_endpoint(client, auth_headers):
    # 1. Create show
    show_resp = client.post("/api/v1/shows", json={
        "title": "Artwork Test Show",
        "slug": "art-test-show",
        "section": "series",
        "status": "draft"
    }, headers=auth_headers)
    assert show_resp.status_code == 201
    show_id = show_resp.json()["id"]

    # 2. Upload valid banner to show
    banner_bytes = _create_test_image(1280, 720, format="JPEG")
    files = {"file": ("banner.jpg", banner_bytes, "image/jpeg")}
    data = {
        "artwork_type": "banner",
        "entity_type": "show",
        "entity_id": show_id
    }
    upload_resp = client.post("/api/v1/artwork/upload", data=data, files=files, headers=auth_headers)
    assert upload_resp.status_code == 201
    art_data = upload_resp.json()
    assert art_data["artwork_type"] == "banner"
    assert art_data["width"] == 1280
    assert art_data["height"] == 720
    assert "/api/v1/storage/" in art_data["url"]

    # 3. Attempt upload of invalid poster (wrong ratio) -> MUST reject (HTTP 422)
    bad_poster_bytes = _create_test_image(1000, 500, format="JPEG")  # Horizontal 2:1
    bad_files = {"file": ("bad_poster.jpg", bad_poster_bytes, "image/jpeg")}
    bad_data = {
        "artwork_type": "poster",
        "entity_type": "show",
        "entity_id": show_id
    }
    bad_upload_resp = client.post("/api/v1/artwork/upload", data=bad_data, files=bad_files, headers=auth_headers)
    assert bad_upload_resp.status_code == 422
    assert "Artwork validation failed" in bad_upload_resp.json()["detail"]["error"]
