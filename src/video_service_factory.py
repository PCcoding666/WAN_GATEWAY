"""
Video Service Factory for Multi-Modal Video Generation.

This module provides a factory for creating appropriate video generation services
based on the generation mode.
"""
import logging
from typing import Optional, Union
from .base_video_service import BaseVideoService
from .text_to_video_service import TextToVideoService
from .image_to_video_service import ImageToVideoService
from .keyframe_to_video_service import KeyFrameVideoService
from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoServiceFactory:
    """Factory for creating video generation services based on mode."""
    
    @staticmethod
    def create_service(mode: str, api_key: Optional[str] = None) -> BaseVideoService:
        """
        Create a video service instance based on the generation mode.
        
        Args:
            mode: Generation mode ('text_to_video', 'image_to_video', 'keyframe_to_video')
            api_key: Optional API key override
            
        Returns:
            BaseVideoService: Appropriate service instance
            
        Raises:
            ValueError: If mode is not supported
        """
        mode = mode.lower().strip()
        
        if mode == "text_to_video":
            logger.info("Creating TextToVideoService")
            return TextToVideoService(api_key)
        elif mode == "image_to_video":
            logger.info("Creating ImageToVideoService")
            return ImageToVideoService(api_key)
        elif mode == "keyframe_to_video":
            logger.info("Creating KeyFrameVideoService")
            return KeyFrameVideoService(api_key)
        else:
            supported_modes = ["text_to_video", "image_to_video", "keyframe_to_video"]
            raise ValueError(f"Unsupported generation mode: {mode}. Supported modes: {supported_modes}")
    
    @staticmethod
    def get_supported_modes() -> list[str]:
        """
        Get list of supported generation modes.
        
        Returns:
            list: List of supported mode strings
        """
        return ["text_to_video", "image_to_video", "keyframe_to_video"]
    
    @staticmethod
    def get_mode_description(mode: str) -> str:
        """
        Get human-readable description for a generation mode.
        
        Args:
            mode: Generation mode string
            
        Returns:
            str: Description of the mode
        """
        descriptions = {
            "text_to_video": "Generate videos from text descriptions",
            "image_to_video": "Generate videos from a single starting image",
            "keyframe_to_video": "Generate videos from start and end frame images"
        }
        return descriptions.get(mode, "Unknown mode")
    
    @staticmethod
    def get_mode_models(mode: str) -> list[str]:
        """
        Get list of available models for a specific generation mode.
        
        Args:
            mode: Generation mode string
            
        Returns:
            list: List of model IDs available for this mode
        """
        if mode == "text_to_video":
            return Config.get_text_to_video_models()
        elif mode == "image_to_video":
            return Config.get_image_to_video_models()
        elif mode == "keyframe_to_video":
            return Config.get_keyframe_to_video_models()
        else:
            return []
    
    @staticmethod
    def get_default_model(mode: str) -> str:
        """
        Get the default model for a specific generation mode.
        
        Args:
            mode: Generation mode string
            
        Returns:
            str: Default model ID for this mode
        """
        models = VideoServiceFactory.get_mode_models(mode)
        if not models:
            return Config.DEFAULT_MODEL
        
        if mode == "text_to_video":
            return Config.DEFAULT_MODEL if Config.DEFAULT_MODEL in models else models[0]
        elif mode == "image_to_video":
            return "wan2.2-i2v-plus" if "wan2.2-i2v-plus" in models else models[0]
        else:
            # For keyframe modes, return the keyframe model
            return "wanx2.1-kf2v-plus" if "wanx2.1-kf2v-plus" in models else models[0]
    
    @staticmethod
    def validate_mode_and_model(mode: str, model: str) -> Optional[str]:
        """
        Validate that a model is compatible with a generation mode.
        
        Args:
            mode: Generation mode string
            model: Model ID string
            
        Returns:
            Optional[str]: Error message if invalid, None if valid
        """
        if mode not in VideoServiceFactory.get_supported_modes():
            return f"Unsupported generation mode: {mode}"
        
        available_models = VideoServiceFactory.get_mode_models(mode)
        if model not in available_models:
            return f"Model {model} is not available for {mode} mode. Available models: {', '.join(available_models)}"
        
        return None

class MultiModalVideoApp:
    """Enhanced application class supporting multiple video generation modes."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the multi-modal video application.
        
        Args:
            api_key: Optional API key override
        """
        self.api_key = api_key
        self.current_service: Optional[BaseVideoService] = None
        self.current_mode: Optional[str] = None
        logger.info("Multi-modal video application initialized")
    
    def set_mode(self, mode: str) -> None:
        """
        Set the current generation mode and create appropriate service.
        
        Args:
            mode: Generation mode to switch to
        """
        if mode != self.current_mode:
            self.current_service = VideoServiceFactory.create_service(mode, self.api_key)
            self.current_mode = mode
            logger.info(f"Switched to {mode} mode")
    
    def generate_video(self, mode: str, **kwargs):
        """
        Generate video using the specified mode and parameters.
        
        Args:
            mode: Generation mode
            **kwargs: Mode-specific parameters
            
        Returns:
            VideoResult: Generation result
        """
        self.set_mode(mode)
        
        if mode == "text_to_video":
            return self.current_service.generate_video(
                prompt=kwargs.get('prompt'),
                style=kwargs.get('style', Config.DEFAULT_STYLE),
                aspect_ratio=kwargs.get('aspect_ratio', Config.DEFAULT_ASPECT_RATIO),
                model=kwargs.get('model', VideoServiceFactory.get_default_model(mode)),
                negative_prompt=kwargs.get('negative_prompt'),
                seed=kwargs.get('seed')
            )
        elif mode == "image_to_video":
            return self.current_service.generate_video(
                image_file=kwargs.get('image_file'),
                prompt=kwargs.get('prompt', ''),
                style=kwargs.get('style', Config.DEFAULT_STYLE),
                model=kwargs.get('model', VideoServiceFactory.get_default_model(mode))
            )
        elif mode == "keyframe_to_video":
            return self.current_service.generate_video(
                start_frame_file=kwargs.get('start_frame_file'),
                end_frame_file=kwargs.get('end_frame_file'),
                prompt=kwargs.get('prompt', ''),
                style=kwargs.get('style', Config.DEFAULT_STYLE),
                model=kwargs.get('model', VideoServiceFactory.get_default_model(mode))
            )
        else:
            raise ValueError(f"Unsupported mode: {mode}")
    
    def get_service_status(self) -> dict:
        """
        Get status information for all services.
        
        Returns:
            dict: Status information
        """
        status = {
            'supported_modes': VideoServiceFactory.get_supported_modes(),
            'current_mode': self.current_mode,
            'api_configured': bool(self.api_key),
            'modes_info': {}
        }
        
        for mode in VideoServiceFactory.get_supported_modes():
            status['modes_info'][mode] = {
                'description': VideoServiceFactory.get_mode_description(mode),
                'available_models': VideoServiceFactory.get_mode_models(mode),
                'default_model': VideoServiceFactory.get_default_model(mode)
            }
        
        return status