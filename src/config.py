"""
Configuration module for Gradio Bailian Text-to-Video Application.

This module manages environment variables, UI options, and API settings.
"""
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration management."""
    
    # API Configuration
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
    API_ENDPOINT = os.getenv(
        'API_ENDPOINT', 
        'https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis'
    )
    
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
            "name": "Wanxiang 2.2 Pro (Recommended)",
            "description": "Latest model with enhanced detail and motion stability",
            "resolutions": ["480P", "1080P"],
            "framerate": "30fps",
            "duration": "5 seconds"
        },
        "wanx2.1-t2v-turbo": {
            "name": "Wanxiang 2.1 Turbo",
            "description": "Fast generation model",
            "resolutions": ["480P", "720P"],
            "framerate": "30fps",
            "duration": "5 seconds"
        },
        "wanx2.1-t2v-plus": {
            "name": "Wanxiang 2.1 Pro",
            "description": "High-quality generation model",
            "resolutions": ["720P"],
            "framerate": "30fps",
            "duration": "5 seconds"
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
    POLLING_INTERVAL = 2  # seconds
    REQUEST_TIMEOUT = 30  # seconds
    MAX_POLL_TIME = 300  # Maximum time to poll for results (5 minutes)
    
    # UI Settings
    MAX_PROMPT_LENGTH = 1000
    DEFAULT_STYLE = "<auto>"
    DEFAULT_ASPECT_RATIO = "16:9"
    DEFAULT_MODEL = "wan2.2-t2v-plus"
    
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
        
        if not cls.API_ENDPOINT:
            raise ValueError("API_ENDPOINT is required")
            
        return True
    
    @classmethod
    def get_style_display_name(cls, style: str) -> str:
        """Get display name for style option."""
        if style == "<auto>":
            return "Auto (Recommended)"
        return style
    
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

# Validate configuration on import
try:
    Config.validate_config()
    print("✓ Configuration validated successfully")
except ValueError as e:
    print(f"✗ Configuration error: {e}")
    raise