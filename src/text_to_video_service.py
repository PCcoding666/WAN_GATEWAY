"""
Text-to-Video Service for Bailian API Integration.

This module provides the core service for generating videos from text
using Alibaba's Bailian wan-v1-t2v API.
"""
import asyncio
import json
import time
import logging
import os
import tempfile
from urllib.parse import urlparse
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import requests
from .config import Config
from .base_video_service import BaseVideoService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VideoResult:
    """Result of video generation."""
    success: bool
    video_url: Optional[str] = None
    local_video_path: Optional[str] = None
    error_message: Optional[str] = None
    task_id: Optional[str] = None
    generation_time: Optional[float] = None
    generation_mode: Optional[str] = None  # New field: text_to_video, image_to_video, keyframe_to_video
    model_used: Optional[str] = None       # New field: which model was used
    input_metadata: Optional[dict] = None  # New field: metadata about inputs (prompts, image info, etc.)

class TextToVideoService(BaseVideoService):
    """Service for generating videos from text using Bailian API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TextToVideoService.
        
        Args:
            api_key: Optional API key override. If not provided, uses Config.DASHSCOPE_API_KEY
        """
        super().__init__(api_key)
        self.base_url = Config.TEXT_TO_VIDEO_ENDPOINT
    
    def get_api_endpoint(self) -> str:
        """Get the API endpoint for text-to-video generation."""
        return self.base_url
    
    def get_polling_interval(self) -> int:
        """Get the polling interval for text-to-video generation."""
        return Config.POLLING_INTERVAL
    
    def get_max_poll_time(self) -> int:
        """Get the maximum polling time for text-to-video generation."""
        return Config.MAX_POLL_TIME
    
    def generate_video(
        self, 
        prompt: str,
        style: str = Config.DEFAULT_STYLE,
        aspect_ratio: str = Config.DEFAULT_ASPECT_RATIO,
        model: str = Config.DEFAULT_MODEL,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None
    ) -> VideoResult:
        """
        Generate video from text prompt.
        
        Args:
            prompt: Text description for video generation
            style: Video style (default from config)
            aspect_ratio: Video aspect ratio (default from config)
            model: Model to use for generation (default from config)
            negative_prompt: Optional negative prompt
            seed: Optional seed for reproducibility
            
        Returns:
            VideoResult with success status and video URL or error message
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            validation_error = self._validate_inputs(prompt, style, aspect_ratio, model)
            if validation_error:
                return VideoResult(
                    success=False,
                    error_message=validation_error
                )
            
            # Build request payload
            request_data = self._build_request(
                prompt=prompt.strip(),
                style=style,
                aspect_ratio=aspect_ratio,
                model=model,
                negative_prompt=negative_prompt,
                seed=seed
            )
            
            logger.info(f"Initiating video generation for prompt: {prompt[:50]}...")
            
            # Submit generation task
            task_response = self._submit_task(request_data)
            if not task_response.get('success', False):
                return VideoResult(
                    success=False,
                    error_message=task_response.get('error', 'Failed to submit generation task')
                )
            
            task_id = task_response.get('task_id')
            if not task_id:
                return VideoResult(
                    success=False,
                    error_message="No task ID received from API"
                )
            
            # Poll for results
            video_url = self._poll_task_result(task_id)
            
            generation_time = time.time() - start_time
            
            if video_url:
                logger.info(f"Video generation completed in {generation_time:.2f} seconds")
                
                # Download video locally to avoid OSS connection issues
                local_path = self._download_video_locally(video_url, task_id)
                
                return VideoResult(
                    success=True,
                    video_url=video_url,
                    local_video_path=local_path,
                    task_id=task_id,
                    generation_time=generation_time,
                    generation_mode="text_to_video",
                    model_used=model,
                    input_metadata={
                        "prompt": prompt,
                        "style": style,
                        "aspect_ratio": aspect_ratio,
                        "negative_prompt": negative_prompt,
                        "seed": seed
                    }
                )
            else:
                return VideoResult(
                    success=False,
                    error_message="Video generation failed or timed out",
                    task_id=task_id
                )
                
        except Exception as e:
            logger.error(f"Video generation error: {str(e)}")
            return VideoResult(
                success=False,
                error_message=f"Generation failed: {str(e)}"
            )
    
    def _validate_inputs(
        self, 
        prompt: str, 
        style: str, 
        aspect_ratio: str,
        model: str
    ) -> Optional[str]:
        """
        Validate input parameters.
        
        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        if not prompt or not prompt.strip():
            return "Prompt cannot be empty"
        
        if len(prompt.strip()) > Config.MAX_PROMPT_LENGTH:
            return f"Prompt too long. Maximum {Config.MAX_PROMPT_LENGTH} characters allowed"
        
        if style not in Config.STYLE_OPTIONS:
            return f"Invalid style. Must be one of: {', '.join(Config.STYLE_OPTIONS)}"
        
        if aspect_ratio not in Config.ASPECT_RATIO_OPTIONS:
            return f"Invalid aspect ratio. Must be one of: {', '.join(Config.ASPECT_RATIO_OPTIONS)}"
        
        if model not in Config.get_text_to_video_models():
            return f"Invalid model. Must be one of: {', '.join(Config.get_text_to_video_models())}"
        
        return None
    
    def _build_request(
        self,
        prompt: str,
        style: str,
        aspect_ratio: str,
        model: str,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None
    ) -> dict:
        """
        Build API request payload.
        
        Returns:
            dict: Formatted request payload
        """
        request_data = {
            "model": model,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "size": self._get_resolution_from_aspect_ratio(aspect_ratio, model)
            }
        }
        
        # Add optional parameters
        if negative_prompt and negative_prompt.strip():
            request_data["parameters"]["negative_prompt"] = negative_prompt.strip()
        
        if seed is not None:
            request_data["parameters"]["seed"] = seed
        
        return request_data
    
    def _submit_task(self, request_data: dict) -> dict:
        """
        Submit video generation task to API.
        
        Returns:
            dict: Response containing task_id or error information
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-DashScope-Async': 'enable'
        }
        
        try:
            logger.info(f"Submitting task to: {self.base_url}")
            logger.info(f"Request payload: {json.dumps(request_data, indent=2)}")
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=request_data,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if 'output' in result and 'task_id' in result['output']:
                    task_id = result['output']['task_id']
                    logger.info(f"Task submitted successfully with ID: {task_id}")
                    return {
                        'success': True,
                        'task_id': task_id
                    }
                else:
                    logger.error(f"Invalid response format: {result}")
                    return {
                        'success': False,
                        'error': f'Invalid response format from API: {result}'
                    }
            else:
                error_msg = self._handle_api_error(response)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = 'Request timeout - please try again'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except requests.exceptions.ConnectionError:
            error_msg = 'Connection error - please check your internet connection'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f'Request failed: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _get_resolution_from_aspect_ratio(self, aspect_ratio: str, model: str) -> str:
        """
        Convert aspect ratio to resolution format required by the API based on model capabilities.
        
        Args:
            aspect_ratio: Aspect ratio string (e.g., "16:9", "1:1", "9:16")
            model: Model name to determine supported resolutions
            
        Returns:
            str: Resolution string (e.g., "1920*1080")
        """
        # Get supported resolutions for the model
        supported_resolutions = Config.get_supported_resolutions_for_model(model)
        
        # Define resolution mappings for different quality levels
        if "1080P" in supported_resolutions:
            # Use 1080P resolutions for models that support it
            resolution_map = {
                "16:9": "1920*1080",  # 1080P widescreen
                "1:1": "1440*1440",   # 1080P square
                "9:16": "1080*1920"   # 1080P portrait
            }
        elif "720P" in supported_resolutions:
            # Use 720P resolutions for models that support it
            resolution_map = {
                "16:9": "1280*720",   # 720P widescreen
                "1:1": "960*960",     # 720P square
                "9:16": "720*1280"    # 720P portrait
            }
        else:
            # Default to 480P resolutions
            resolution_map = {
                "16:9": "832*480",    # 480P widescreen
                "1:1": "624*624",     # 480P square
                "9:16": "480*832"     # 480P portrait
            }
        
        return resolution_map.get(aspect_ratio, resolution_map["16:9"])  # Default to 16:9