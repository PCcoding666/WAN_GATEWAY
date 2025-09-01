"""
Configuration module for Gradio Bailian Text-to-Video Application.

This module manages environment variables, UI options, and API settings.
"""
import os
from dotenv import load_dotenv
from typing import List, Optional

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
    
    # Text-to-Video API Configuration
    TEXT_TO_VIDEO_ENDPOINT = os.getenv(
        'TEXT_TO_VIDEO_ENDPOINT', 
        'https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis'
    )
    
    # Image/Keyframe-to-Video API Configuration
    KEYFRAME_VIDEO_ENDPOINT = os.getenv(
        'KEYFRAME_VIDEO_ENDPOINT',
        'https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis'
    )
    
    # Image-to-Video API Configuration (uses different endpoint)
    IMAGE_TO_VIDEO_ENDPOINT = os.getenv(
        'IMAGE_TO_VIDEO_ENDPOINT',
        'https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis'
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
    
    # UI Configuration - Model Options
    MODEL_OPTIONS: dict = {
        "wan2.2-t2v-plus": {
            "name": "wan2.2-t2v-plus",
            "description": "Latest model with enhanced detail and motion stability",
            "resolutions": ["480P", "1080P"],
            "framerate": "30fps",
            "duration": "5 seconds",
            "api_type": "text_to_video"
        },
        "wanx2.1-t2v-turbo": {
            "name": "wanx2.1-t2v-turbo",
            "description": "Fast generation model",
            "resolutions": ["480P", "720P"],
            "framerate": "30fps",
            "duration": "5 seconds",
            "api_type": "text_to_video"
        },
        "wanx2.1-t2v-plus": {
            "name": "wanx2.1-t2v-plus",
            "description": "High-quality generation model",
            "resolutions": ["720P"],
            "framerate": "30fps",
            "duration": "5 seconds",
            "api_type": "text_to_video"
        },
        "wan2.2-i2v-flash": {
            "name": "wan2.2-i2v-flash",
            "description": "Fastest generation speed with enhanced instruction understanding",
            "resolutions": ["480P", "720P"],
            "framerate": "30fps",
            "duration": "5 seconds",
            "api_type": "image_to_video"
        },
        "wan2.2-i2v-plus": {
            "name": "wan2.2-i2v-plus",
            "description": "Latest image-to-video generation model",
            "resolutions": ["480P", "1080P"],
            "framerate": "30fps",
            "duration": "5 seconds",
            "api_type": "image_to_video"
        },
        "wanx2.1-i2v-plus": {
            "name": "wanx2.1-i2v-plus",
            "description": "Complex motion with detailed physics",
            "resolutions": ["720P"],
            "framerate": "30fps",
            "duration": "5 seconds",
            "api_type": "image_to_video"
        },
        "wanx2.1-i2v-turbo": {
            "name": "wanx2.1-i2v-turbo",
            "description": "Fast generation with complex motion support",
            "resolutions": ["480P", "720P"],
            "framerate": "30fps",
            "duration": "3-5 seconds",
            "api_type": "image_to_video"
        },
        "wanx2.1-kf2v-plus": {
            "name": "wanx2.1-kf2v-plus",
            "description": "Keyframe-to-video generation model",
            "resolutions": ["720P"],
            "framerate": "30fps",
            "duration": "5 seconds",
            "api_type": "keyframe_to_video"
        }
    }
    
    # UI Configuration - Aspect Ratio Options
    ASPECT_RATIO_OPTIONS: List[str] = [
        "16:9",    # Widescreen format
        "1:1",     # Square format
        "9:16"     # Portrait/mobile format
    ]
    
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
    MAX_PROMPT_LENGTH = 1000
    DEFAULT_STYLE = "<auto>"
    DEFAULT_ASPECT_RATIO = "16:9"
    DEFAULT_MODEL = "wan2.2-t2v-plus"
    DEFAULT_IMAGE_TO_VIDEO_MODEL = "wan2.2-i2v-flash"  # Recommended fastest model
    
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
            "1:1": "1:1 (Square)",
            "9:16": "9:16 (Portrait)"
        }
        return ratio_names.get(ratio, ratio)
    
    @classmethod
    def get_model_display_name(cls, model_id: str) -> str:
        """Get display name for model option."""
        if model_id in cls.MODEL_OPTIONS:
            return cls.MODEL_OPTIONS[model_id]["name"]
        return model_id
    
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
    def get_api_type_for_model(cls, model_id: str) -> str:
        """Get API type for a specific model."""
        if model_id in cls.MODEL_OPTIONS:
            return cls.MODEL_OPTIONS[model_id].get("api_type", "text_to_video")
        return "text_to_video"
    
    @classmethod
    def get_text_to_video_models(cls) -> List[str]:
        """Get list of models that support text-to-video generation."""
        return [model_id for model_id, info in cls.MODEL_OPTIONS.items() 
                if info.get("api_type") == "text_to_video"]
    
    @classmethod
    def get_image_to_video_models(cls) -> List[str]:
        """Get list of models that support image-to-video generation."""
        return [model_id for model_id, info in cls.MODEL_OPTIONS.items() 
                if info.get("api_type") == "image_to_video"]
    
    @classmethod
    def get_keyframe_to_video_models(cls) -> List[str]:
        """Get list of models that support keyframe-to-video generation."""
        return [model_id for model_id, info in cls.MODEL_OPTIONS.items() 
                if info.get("api_type") == "keyframe_to_video"]
    
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

# Validate configuration on import
try:
    Config.validate_config()
    print("✓ Configuration validated successfully")
except ValueError as e:
    print(f"✗ Configuration error: {e}")
    raise