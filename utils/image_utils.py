"""Image processing utilities."""

import io
import os
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

from config.settings import config


def validate_image(file_path: str) -> Tuple[bool, str]:
    """
    Validate that a file is a supported image format.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, "文件不存在"
    
    ext = Path(file_path).suffix.lower()
    if ext not in config.supported_formats:
        return False, f"不支持的图片格式: {ext}，仅支持 {', '.join(config.supported_formats)}"
    
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > config.max_image_size_mb:
            return False, f"图片文件过大 ({file_size_mb:.1f}MB)，最大支持 {config.max_image_size_mb}MB"
        
        with Image.open(file_path) as img:
            img.verify()
        return True, ""
    except Exception as e:
        return False, f"图片文件损坏或无法读取: {str(e)}"


def load_image(file_path: str) -> Optional[Image.Image]:
    """Load an image file and return a PIL Image object."""
    try:
        return Image.open(file_path).convert("RGB")
    except Exception:
        return None


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """Convert a PIL Image to bytes."""
    buf = io.BytesIO()
    image.save(buf, format=format)
    return buf.getvalue()


def get_image_info(file_path: str) -> dict:
    """Get basic information about an image."""
    try:
        with Image.open(file_path) as img:
            return {
                "format": img.format,
                "mode": img.mode,
                "size": img.size,  # (width, height)
                "width": img.width,
                "height": img.height,
            }
    except Exception as e:
        return {"error": str(e)}
