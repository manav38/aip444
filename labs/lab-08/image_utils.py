import base64
import io
import os
from pathlib import Path
from typing import Dict

from PIL import Image


MAX_SIZE = 1024
JPEG_QUALITY = 85


def process_image(path: str) -> Dict[str, object]:
    image_path = Path(path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    original_size = image_path.stat().st_size

    with Image.open(image_path) as img:
        original_dimensions = img.size

        img = img.convert("RGB")
        img.thumbnail((MAX_SIZE, MAX_SIZE))

        processed_dimensions = img.size

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=JPEG_QUALITY)

        processed_bytes = buffer.getvalue()
        processed_size = len(processed_bytes)

        base64_string = base64.b64encode(processed_bytes).decode("utf-8")
        base64_size = len(base64_string)

    return {
        "base64": base64_string,
        "original_size": original_size,
        "processed_size": processed_size,
        "base64_size": base64_size,
        "original_dimensions": original_dimensions,
        "processed_dimensions": processed_dimensions,
    }


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} bytes"

    if size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"

    return f"{size / (1024 * 1024):.2f} MB"