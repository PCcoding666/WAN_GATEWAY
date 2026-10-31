"""
Configuration module for Gradio Bailian Text-to-Video Application.

This module manages environment variables, UI options, and API settings.
"""
import os
from dotenv import load_dotenv
from typing import List, Optional

from . import models as _models

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration management."""
    
    # API Configuration
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
    
    # OSS Configuration for Image Upload
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
    OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com')
    OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', 'wan-gateway-images')
    OSS_ENABLE = all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME])

    # DashScope region. ``cn`` (Beijing, default) or ``intl`` (Singapore).
    # DASHSCOPE_BASE_URL overrides the host completely.
    DASHSCOPE_REGION = os.getenv('DASHSCOPE_REGION', 'cn').lower()
    _REGION_HOSTS = {
        'cn': 'https://dashscope.aliyuncs.com',
        'intl': 'https://dashscope-intl.aliyuncs.com',
    }
    DASHSCOPE_BASE_URL = os.getenv('DASHSCOPE_BASE_URL', _REGION_HOSTS.get(DASHSCOPE_REGION, _REGION_HOSTS['cn']))
    TASKS_ENDPOINT = f"{DASHSCOPE_BASE_URL}/api/v1/tasks"

    # Local data: task history + downloaded videos (survive page refreshes)
    DATA_DIR = os.path.expanduser(os.getenv('WAN_DATA_DIR', '~/.wan_gateway'))
    VIDEO_DIR = os.path.join(DATA_DIR, 'videos')
    HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')
    HISTORY_LIMIT = int(os.getenv('WAN_HISTORY_LIMIT', '50'))

    # Show legacy (2.2 / 2.5) and deprecated (2.1) models in the UI
    SHOW_LEGACY_MODELS = os.getenv('WAN_SHOW_LEGACY', '0') in ('1', 'true', 'yes')
    SHOW_DEPRECATED_MODELS = os.getenv('WAN_SHOW_DEPRECATED', '0') in ('1', 'true', 'yes')

    # Qwen model used by the ✨ Enhance button
    PROMPT_OPTIMIZER_MODEL = os.getenv('WAN_PROMPT_OPTIMIZER_MODEL', 'qwen-plus')

    # Never call the API; just show the payload (handy for CI / demos)
    DRY_RUN = os.getenv('WAN_DRY_RUN', '0') in ('1', 'true', 'yes')
    
    # Text-to-Video API Configuration
    TEXT_TO_VIDEO_ENDPOINT = os.getenv(
        'TEXT_TO_VIDEO_ENDPOINT', 
        f'{DASHSCOPE_BASE_URL}/api/v1/services/aigc/video-generation/video-synthesis'
    )
    
    # Image/Keyframe-to-Video API Configuration
    KEYFRAME_VIDEO_ENDPOINT = os.getenv(
        'KEYFRAME_VIDEO_ENDPOINT',
        f'{DASHSCOPE_BASE_URL}/api/v1/services/aigc/image2video/video-synthesis'
    )
    
    # Image-to-Video API Configuration (uses different endpoint)
    IMAGE_TO_VIDEO_ENDPOINT = os.getenv(
        'IMAGE_TO_VIDEO_ENDPOINT',
        f'{DASHSCOPE_BASE_URL}/api/v1/services/aigc/video-generation/video-synthesis'
    )
    
    # Legacy API endpoint (for backward compatibility)
    API_ENDPOINT = TEXT_TO_VIDEO_ENDPOINT
    
    # UI Configuration - Style Options
    STYLE_OPTIONS: List[str] = [
        "<auto>",           # Automatic style selection
        "Cinematic",        # Movie-like quality
        "Anime",           # Animation style
        "Realistic",       # Photorealistic
        "Abstract",        # Artistic abstract
        "Documentary",     # Documentary style
        "Commercial"       # Advertisement style
    ]
    
    # UI Configuration - Model Options (derived from src/models.py registry,
    # kept for backward compatibility with older callers / docs)
    MODEL_OPTIONS: dict = {
        spec.id: {
            "name": spec.id,
            "description": spec.description,
            "resolutions": list(spec.resolutions),
            "framerate": f"{spec.fps}fps",
            "duration": spec.duration_label,
            "api_type": {
                _models.T2V: "text_to_video",
                _models.I2V: "image_to_video",
                _models.KF2V: "keyframe_to_video",
                _models.R2V: "reference_to_video",
            }[spec.tasks[0]] if spec.id != "wan3.0-video" else "text_to_video",
            "tasks": list(spec.tasks),
            "supports_audio": spec.audio,
            "max_prompt_length": spec.max_prompt,
            "resolution_format": "label" if spec.dialect in ("label", "media", "kf2v") else "size",
            "status": spec.status,
            "family": spec.family,
        }
        for spec in _models.REGISTRY.values()
    }
    
    # UI Configuration - Aspect Ratio Options
    ASPECT_RATIO_OPTIONS: List[str] = list(_models.ALL_RATIOS) + ["adaptive"]
    
    # API Settings
    MAX_RETRIES = 3
    POLLING_INTERVAL = 2  # seconds for text-to-video
    KEYFRAME_POLLING_INTERVAL = 30  # seconds for image/keyframe-to-video (longer processing time)
    REQUEST_TIMEOUT = 30  # seconds
    MAX_POLL_TIME = 300  # Maximum time to poll for text-to-video results (5 minutes)
    KEYFRAME_MAX_POLL_TIME = 900  # Maximum time to poll for keyframe results (15 minutes)
    
    # Image Upload Configuration
    IMAGE_UPLOAD_CONFIG = {
        "max_size_mb": 10,
        "allowed_formats": ["JPEG", "JPG", "PNG", "BMP", "WEBP"],
        "min_dimension": 360,
        "max_dimension": 2000,
        "temp_storage_hours": 1
    }
    
    # UI Settings
    MAX_PROMPT_LENGTH = 2000
    DEFAULT_STYLE = "<auto>"
    DEFAULT_ASPECT_RATIO = "16:9"
    DEFAULT_MODEL = os.getenv('WAN_DEFAULT_T2V_MODEL', _models.default_model_for_task(_models.T2V))
    DEFAULT_IMAGE_TO_VIDEO_MODEL = os.getenv('WAN_DEFAULT_I2V_MODEL', _models.default_model_for_task(_models.I2V))
    DEFAULT_KEYFRAME_TO_VIDEO_MODEL = os.getenv('WAN_DEFAULT_KF2V_MODEL', _models.default_model_for_task(_models.KF2V))
    DEFAULT_REFERENCE_TO_VIDEO_MODEL = os.getenv('WAN_DEFAULT_R2V_MODEL', _models.default_model_for_task(_models.R2V))
    
    # Duration / audio defaults (per-model limits live in src/models.py)
    DEFAULT_DURATION = 5
    DURATION_OPTIONS = [5, 10]  # kept for Wan 2.5 callers
    DEFAULT_AUDIO_ENABLED = True
    
    # Video File Management
    VIDEO_CACHE_MAX_AGE_HOURS = 24  # Clean up videos older than 24 hours
    VIDEO_DOWNLOAD_TIMEOUT_MULTIPLIER = 3  # Multiply REQUEST_TIMEOUT for video downloads
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate required configuration is present.
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.DASHSCOPE_API_KEY:
            raise ValueError(
                "DASHSCOPE_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )
        
        if not cls.TEXT_TO_VIDEO_ENDPOINT:
            raise ValueError("TEXT_TO_VIDEO_ENDPOINT is required")
            
        if not cls.KEYFRAME_VIDEO_ENDPOINT:
            raise ValueError("KEYFRAME_VIDEO_ENDPOINT is required")
            
        return True
    
    @classmethod
    def get_style_display_name(cls, style: str) -> str:
        """Get display name for style option."""
        if style == "<auto>":
            return "Auto (Recommended)"
        return style
    
    @classmethod
    def get_style_value_from_display(cls, display_name: str) -> str:
        """Get actual style value from display name."""
        if display_name == "Auto (Recommended)":
            return "<auto>"
        return display_name
    
    @classmethod
    def get_aspect_ratio_display_name(cls, ratio: str) -> str:
        """Get display name for aspect ratio option."""
        ratio_names = {
            "16:9": "16:9 (Widescreen)",
            "9:16": "9:16 (Portrait)",
            "1:1": "1:1 (Square)",
            "4:3": "4:3 (Classic)",
            "3:4": "3:4 (Tall)",
            "adaptive": "Adaptive (follow input)",
        }
        return ratio_names.get(ratio, ratio)
    
    @classmethod
    def get_model_display_name(cls, model_id: str) -> str:
        """Get display name for model option."""
        if model_id in cls.MODEL_OPTIONS:
            return cls.MODEL_OPTIONS[model_id]["name"]
        return model_id
    
    @classmethod
    def get_model_id_from_display_name(cls, display_name: str) -> str:
        """Get model ID from display name."""
        for model_id, info in cls.MODEL_OPTIONS.items():
            if info["name"] == display_name:
                return model_id
        return display_name  # Return as-is if not found
    
    @classmethod
    def get_model_description(cls, model_id: str) -> str:
        """Get description for model option."""
        if model_id in cls.MODEL_OPTIONS:
            return cls.MODEL_OPTIONS[model_id]["description"]
        return ""
    
    @classmethod
    def get_supported_resolutions_for_model(cls, model_id: str) -> List[str]:
        """Get supported resolutions for a specific model."""
        if model_id in cls.MODEL_OPTIONS:
            return cls.MODEL_OPTIONS[model_id]["resolutions"]
        return ["480P", "720P", "1080P"]
    
    @classmethod
    def supports_audio(cls, model_id: str) -> bool:
        """Check if model supports audio generation."""
        if model_id in cls.MODEL_OPTIONS:
            return cls.MODEL_OPTIONS[model_id].get("supports_audio", False)
        return False
    
    @classmethod
    def get_max_prompt_length(cls, model_id: str) -> int:
        """Get maximum prompt length for a specific model."""
        if model_id in cls.MODEL_OPTIONS:
            return cls.MODEL_OPTIONS[model_id].get("max_prompt_length", 1000)
        return 1000
    
    @classmethod
    def uses_resolution_label(cls, model_id: str) -> bool:
        """Check if model uses resolution labels (e.g., '480P') instead of dimensions (e.g., '832*480')."""
        if model_id in cls.MODEL_OPTIONS:
            return cls.MODEL_OPTIONS[model_id].get("resolution_format") == "label"
        return False
    
    @classmethod
    def get_api_type_for_model(cls, model_id: str) -> str:
        """Get API type for a specific model."""
        if model_id in cls.MODEL_OPTIONS:
            return cls.MODEL_OPTIONS[model_id].get("api_type", "text_to_video")
        return "text_to_video"
    
    @classmethod
    def _models_for(cls, task: str) -> List[str]:
        include_hidden = cls.SHOW_LEGACY_MODELS or cls.SHOW_DEPRECATED_MODELS
        ids = _models.model_ids_for_task(task, include_hidden=True)
        if include_hidden:
            if not cls.SHOW_DEPRECATED_MODELS:
                ids = [m for m in ids if _models.get_spec(m).status != "deprecated"]
            return ids
        # Always expose everything programmatically; the UI filters by status itself.
        return ids

    @classmethod
    def get_text_to_video_models(cls) -> List[str]:
        """Models that support text-to-video generation."""
        return cls._models_for(_models.T2V)
    
    @classmethod
    def get_image_to_video_models(cls) -> List[str]:
        """Models that support image-to-video (first frame) generation."""
        return cls._models_for(_models.I2V)
    
    @classmethod
    def get_keyframe_to_video_models(cls) -> List[str]:
        """Models that support first+last frame generation."""
        return cls._models_for(_models.KF2V)

    @classmethod
    def get_reference_to_video_models(cls) -> List[str]:
        """Models that support reference-to-video generation."""
        return cls._models_for(_models.R2V)
    
    @classmethod
    def validate_image_upload(cls, file_size_mb: float, format: str, width: int, height: int) -> Optional[str]:
        """Validate image upload parameters."""
        config = cls.IMAGE_UPLOAD_CONFIG
        
        if file_size_mb > config["max_size_mb"]:
            return f"Image file too large. Maximum size: {config['max_size_mb']}MB"
        
        if format.upper() not in config["allowed_formats"]:
            return f"Invalid image format. Allowed formats: {', '.join(config['allowed_formats'])}"
        
        if width < config["min_dimension"] or height < config["min_dimension"]:
            return f"Image dimensions too small. Minimum: {config['min_dimension']}px"
        
        if width > config["max_dimension"] or height > config["max_dimension"]:
            return f"Image dimensions too large. Maximum: {config['max_dimension']}px"
        
        return None

# Validate configuration on import only if running as main script
if __name__ == "__main__":
    try:
        Config.validate_config()
        print("✓ Configuration validated successfully")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        raise