"""
Local vision model for image recognition fallback.

Supports two model locations:
  1. HuggingFace hub cache: .model_cache/models--Salesforce--blip-image-captioning-base/snapshots/...
  2. Direct download:       .model_cache/blip-image-captioning-base/   (user cloned repo)
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

os.environ.setdefault(
    "TRANSFORMERS_CACHE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".model_cache"),
)

MODEL_NAME = "Salesforce/blip-image-captioning-base"


def _local_model_path() -> Optional[str]:
    """
    Find the model on disk. Returns path to the model directory,
    or None if not found.
    
    Checks two locations:
      - huggingface hub cache structure (from_pretrained default)
      - user cloned repo (git clone ... blip-image-captioning-base)
    """
    cache_dir = os.environ.get("TRANSFORMERS_CACHE", "")
    project_root = os.path.dirname(os.path.dirname(__file__))

    candidates = []

    # Path 1: huggingface hub cache structure
    if cache_dir:
        hub_path = os.path.join(cache_dir, f"models--{MODEL_NAME.replace('/', '--')}", "snapshots")
        candidates.append(hub_path)
        # Also check without 'snapshots'
        candidates.append(os.path.join(cache_dir, f"models--{MODEL_NAME.replace('/', '--')}"))

    # Path 2: user cloned the repo directly under .model_cache
    candidates.append(os.path.join(project_root, ".model_cache", "blip-image-captioning-base"))

    # Path 3: user cloned directly in project root
    candidates.append(os.path.join(project_root, "blip-image-captioning-base"))

    for path in candidates:
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "config.json")):
            # If it's a hub snapshot dir, go up one level for the model dir
            if path.endswith("snapshots"):
                snap_subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
                if snap_subdirs:
                    return os.path.join(path, snap_subdirs[0])
                continue
            return path

    return None


class LocalVisionModel:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._processor = None
        self._model = None
        self._available = False
        self._init_error = None

    def _load(self) -> bool:
        if self._available:
            return True

        # Check Python deps
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
        except ImportError:
            self._init_error = "need: pip install torch transformers accelerate"
            logger.warning(self._init_error)
            return False

        # Find model on disk
        local_path = _local_model_path()
        if not local_path:
            cache_dir = os.environ.get("TRANSFORMERS_CACHE", "")
            self._init_error = (
                f"Model not found on disk.\n"
                f"Expected locations checked:\n"
                f"  {cache_dir}\n"
                f"  .model_cache/blip-image-captioning-base/\n"
                f"To download: cd .model_cache && git clone https://hf-mirror.com/{MODEL_NAME}"
            )
            logger.info(f"Vision model not found on disk. Checked: {cache_dir}")
            return False

        # Load from local path
        try:
            logger.info(f"Loading vision model from: {local_path}")
            self._processor = BlipProcessor.from_pretrained(local_path, local_files_only=True)
            self._model = BlipForConditionalGeneration.from_pretrained(local_path, local_files_only=True)
            self._available = True
            logger.info("Vision model loaded successfully")
            return True
        except Exception as e:
            self._init_error = f"Failed to load model from {local_path}: {e}"
            logger.error(self._init_error)
            return False

    def describe_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        if not self._load():
            return None
        try:
            from PIL import Image
            img = Image.open(image_path).convert("RGB")
            inputs = self._processor(img, return_tensors="pt")
            out = self._model.generate(**inputs, max_new_tokens=50)
            cap = self._processor.decode(out[0], skip_special_tokens=True)
            return {"caption": cap, "details": f"Scene: {cap}", "model": self.model_name}
        except Exception as e:
            logger.error(f"describe failed: {e}")
            return None

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def error_message(self) -> Optional[str]:
        return self._init_error


_local_vision_model: Optional[LocalVisionModel] = None


def get_vision_model() -> LocalVisionModel:
    global _local_vision_model
    if _local_vision_model is None:
        _local_vision_model = LocalVisionModel()
    return _local_vision_model


def describe_image_local(image_path: str) -> Optional[str]:
    model = get_vision_model()
    result = model.describe_image(image_path)
    return result["details"] if result else None
