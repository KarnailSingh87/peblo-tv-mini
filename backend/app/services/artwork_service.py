import io
from typing import Dict, Any, List, Tuple
from PIL import Image
from backend.app.core.config import settings

class ArtworkValidationResult:
    def __init__(
        self,
        is_valid: bool,
        artwork_type: str,
        width: int = 0,
        height: int = 0,
        aspect_ratio: float = 0.0,
        file_size_bytes: int = 0,
        mime_type: str = "image/jpeg",
        errors: List[str] = None
    ):
        self.is_valid = is_valid
        self.artwork_type = artwork_type
        self.width = width
        self.height = height
        self.aspect_ratio = aspect_ratio
        self.file_size_bytes = file_size_bytes
        self.mime_type = mime_type
        self.errors = errors or []

class ArtworkService:
    """
    Validates artwork files against reference.json constraints:
    - Poster: 2:3 vertical aspect ratio (~600x900px, max 200 KB)
    - Banner: 16:9 widescreen aspect ratio (~1280x720px, max 200 KB)
    - Thumbnail: 16:9 landscape aspect ratio (~640x360px, max 200 KB)
    """

    SPECS = {
        "poster": {
            "name": "Poster",
            "expected_aspect": 2 / 3,  # 0.6667
            "ratio_str": "2:3 (vertical)",
            "target_dim": (600, 900),
            "min_dim": (400, 600),
            "tolerance": 0.08,  # [0.58, 0.75]
            "max_kb": 200
        },
        "banner": {
            "name": "Hero Banner",
            "expected_aspect": 16 / 9,  # 1.7778
            "ratio_str": "16:9 (widescreen)",
            "target_dim": (1280, 720),
            "min_dim": (800, 450),
            "tolerance": 0.15,  # [1.62, 1.93]
            "max_kb": 200
        },
        "thumbnail": {
            "name": "Episode Thumbnail",
            "expected_aspect": 16 / 9,  # 1.7778
            "ratio_str": "16:9 (landscape)",
            "target_dim": (640, 360),
            "min_dim": (480, 270),
            "tolerance": 0.15,  # [1.62, 1.93]
            "max_kb": 200
        }
    }

    @classmethod
    def validate_artwork(cls, file_bytes: bytes, artwork_type: str, filename: str = "") -> ArtworkValidationResult:
        errors: List[str] = []
        file_size = len(file_bytes)
        art_type = artwork_type.lower().strip()

        # 1. Check artwork slot type
        if art_type not in cls.SPECS:
            errors.append(f"Invalid artwork type '{artwork_type}'. Allowed types are: {', '.join(cls.SPECS.keys())}.")
            return ArtworkValidationResult(is_valid=False, artwork_type=art_type, file_size_bytes=file_size, errors=errors)

        spec = cls.SPECS[art_type]
        max_bytes = spec["max_kb"] * 1024

        # 2. Check maximum file size (200 KB)
        if file_size > max_bytes:
            errors.append(
                f"File size ({file_size / 1024:.1f} KB) exceeds the maximum allowed limit of {spec['max_kb']} KB. Please compress your image."
            )

        if file_size == 0:
            errors.append("Uploaded file is empty.")
            return ArtworkValidationResult(is_valid=False, artwork_type=art_type, file_size_bytes=file_size, errors=errors)

        # 3. Validate image decodability and format
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image.verify()  # Verify image integrity
            # Reopen after verify
            image = Image.open(io.BytesIO(file_bytes))
            img_format = (image.format or "JPEG").upper()
            width, height = image.size
        except Exception as e:
            errors.append(f"Invalid or corrupted image file format ({str(e)}). Please upload a valid JPG, PNG, or WebP image.")
            return ArtworkValidationResult(is_valid=False, artwork_type=art_type, file_size_bytes=file_size, errors=errors)

        mime_map = {"JPEG": "image/jpeg", "JPG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
        mime_type = mime_map.get(img_format, "image/jpeg")

        # 4. Check minimum dimensions
        min_w, min_h = spec["min_dim"]
        if width < min_w or height < min_h:
            errors.append(
                f"{spec['name']} image is too small ({width}×{height}px). Minimum required dimensions are {min_w}×{min_h}px (target ~{spec['target_dim'][0]}×{spec['target_dim'][1]}px)."
            )

        # 5. Check aspect ratio
        actual_ratio = width / height
        expected_ratio = spec["expected_aspect"]
        tolerance = spec["tolerance"]

        if abs(actual_ratio - expected_ratio) > tolerance:
            if art_type == "poster" and actual_ratio > 1.0:
                errors.append(
                    f"Poster must be vertical with a {spec['ratio_str']} aspect ratio (e.g. {spec['target_dim'][0]}×{spec['target_dim'][1]}px). The uploaded image is horizontal ({width}×{height}px)."
                )
            elif art_type in ["banner", "thumbnail"] and actual_ratio < 1.0:
                errors.append(
                    f"{spec['name']} must be horizontal with a {spec['ratio_str']} aspect ratio (e.g. {spec['target_dim'][0]}×{spec['target_dim'][1]}px). The uploaded image is vertical ({width}×{height}px)."
                )
            else:
                errors.append(
                    f"Invalid aspect ratio ({actual_ratio:.2f}). {spec['name']} requires a {spec['ratio_str']} ratio (target: ~{spec['target_dim'][0]}×{spec['target_dim'][1]}px)."
                )

        return ArtworkValidationResult(
            is_valid=(len(errors) == 0),
            artwork_type=art_type,
            width=width,
            height=height,
            aspect_ratio=actual_ratio,
            file_size_bytes=file_size,
            mime_type=mime_type,
            errors=errors
        )
