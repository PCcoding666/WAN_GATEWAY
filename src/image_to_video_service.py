"""
Image-to-Video Service for Bailian API Integration.

This module provides the service for generating videos from a single image
using Alibaba's Bailian wan-kf2v API.
"""
import json
import time
import logging
import base64
from typing import Optional
from PIL import Image
import requests
from .config import Config
from .base_video_service import BaseVideoService
from .text_to_video_service import VideoResult
from .oss_service import oss_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageToVideoService(BaseVideoService):
    """Service for generating videos from images using Bailian API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ImageToVideoService.
        
        Args:
            api_key: Optional API key override. If not provided, uses Config.DASHSCOPE_API_KEY
        """
        super().__init__(api_key)
        self.base_url = Config.IMAGE_TO_VIDEO_ENDPOINT
    
    def get_api_endpoint(self) -> str:
        """Get the API endpoint for image-to-video generation."""
        return self.base_url
    
    def get_polling_interval(self) -> int:
        """Get the polling interval for image-to-video generation."""
        return Config.KEYFRAME_POLLING_INTERVAL
    
    def get_max_poll_time(self) -> int:
        """Get the maximum polling time for image-to-video generation."""
        return Config.KEYFRAME_MAX_POLL_TIME
    
    def generate_video(
        self,
        image_file,
        prompt: str = "",
        style: str = Config.DEFAULT_STYLE,
        model: str = "wan2.2-i2v-plus"
    ) -> VideoResult:
        """
        Generate video from a single image.
        
        Args:
            image_file: The uploaded image file (from Gradio)
            prompt: Optional text prompt for guidance
            style: Video style (default from config)
            model: Model to use for generation (must be keyframe model)
            
        Returns:
            VideoResult with success status and video URL or error message
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            validation_error = self._validate_image_inputs(image_file, prompt, model)
            if validation_error:
                return VideoResult(
                    success=False,
                    error_message=validation_error
                )
            
            # Process image and upload to OSS
            public_image_url, image_info = self._process_image_upload(image_file)
            if not public_image_url:
                return VideoResult(
                    success=False,
                    error_message="Failed to process and upload image"
                )
            
            # Build request payload
            request_data = self._build_image_request(
                public_image_url=public_image_url,
                prompt=prompt.strip() if prompt else None,
                model=model
            )
            
            logger.info(f"Initiating image-to-video generation...")
            
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
                    generation_mode="image_to_video",
                    model_used=model,
                    input_metadata={
                        "prompt": prompt,
                        "style": style,
                        "image_info": image_info
                    }
                )
            else:
                return VideoResult(
                    success=False,
                    error_message="Video generation failed or timed out",
                    task_id=task_id
                )
                
        except Exception as e:
            logger.error(f"Image-to-video generation error: {str(e)}")
            return VideoResult(
                success=False,
                error_message=f"Generation failed: {str(e)}"
            )
    
    def _validate_image_inputs(
        self,
        image_file,
        prompt: str,
        model: str
    ) -> Optional[str]:
        """
        Validate input parameters for image-to-video generation.
        
        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        if image_file is None:
            return "Image file is required"
        
        if model not in Config.get_image_to_video_models():
            return f"Invalid model for image-to-video. Must be one of: {', '.join(Config.get_image_to_video_models())}"
        
        if prompt and len(prompt.strip()) > Config.MAX_PROMPT_LENGTH:
            return f"Prompt too long. Maximum {Config.MAX_PROMPT_LENGTH} characters allowed"
        
        return None
    
    def _process_image_upload(self, image_file) -> tuple[Optional[str], Optional[dict]]:
        """
        Process uploaded image and upload to OSS to get public URL.
        
        Args:
            image_file: The uploaded image file from Gradio
            
        Returns:
            tuple: (public_url, image_info) or (None, None) if failed
        """
        try:
            # Validate image file
            if image_file is None:
                logger.error("No image file provided")
                return None, None
            
            # Get basic image info for validation
            with Image.open(image_file) as img:
                width, height = img.size
                original_format = img.format or 'JPEG'
                file_size_mb = image_file.size / (1024 * 1024) if hasattr(image_file, 'size') else 0
                
                # Validate image dimensions and format
                validation_error = Config.validate_image_upload(file_size_mb, original_format, width, height)
                if validation_error:
                    logger.error(f"Image validation failed: {validation_error}")
                    return None, None
            
            # Upload to OSS and get public URL
            public_url, upload_info = oss_service.upload_image(image_file)
            
            if public_url:
                logger.info(f"Image uploaded successfully to OSS: {public_url}")
                
                # Combine validation info with upload info
                image_info = {
                    "public_url": public_url,
                    "original_width": width,
                    "original_height": height,
                    "original_format": original_format,
                    "file_size_mb": file_size_mb,
                    **upload_info
                }
                
                return public_url, image_info
            else:
                logger.error("Failed to upload image to OSS")
                return None, None
                
        except Exception as e:
            logger.error(f"Error processing image upload: {str(e)}")
            return None, None
    
    def _build_image_request(
        self,
        public_image_url: str,
        prompt: Optional[str] = None,
        model: str = "wan2.2-i2v-flash"  # Use recommended fastest model as default
    ) -> dict:
        """
        Build API request payload for image-to-video generation using public URL.
        
        Args:
            public_image_url: Public URL of the uploaded image
            prompt: Optional text prompt
            model: Model to use for generation
            
        Returns:
            dict: Formatted request payload
        """
        # Get supported resolutions for the model
        supported_resolutions = Config.get_supported_resolutions_for_model(model)
        
        # Choose appropriate resolution based on model capabilities
        if "1080P" in supported_resolutions:
            resolution = "1080P"
        elif "720P" in supported_resolutions:
            resolution = "720P"
        elif "480P" in supported_resolutions:
            resolution = "480P"
        else:
            resolution = supported_resolutions[0] if supported_resolutions else "480P"
        
        request_data = {
            "model": model,
            "input": {
                "img_url": public_image_url
            },
            "parameters": {
                "resolution": resolution,
                "prompt_extend": True
            }
        }
        
        # Add optional prompt
        if prompt and prompt.strip():
            request_data["input"]["prompt"] = prompt.strip()
        
        logger.info(f"Using model: {model}, resolution: {resolution}")
        logger.info(f"Image URL: {public_image_url}")
        
        return request_data
    
    def _submit_task(self, request_data: dict) -> dict:
        """
        Submit image-to-video generation task to API.
        
        Returns:
            dict: Response containing task_id or error information
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-DashScope-Async': 'enable'
        }
        
        try:
            logger.info(f"Submitting image-to-video task to: {self.base_url}")
            # Log the full request payload since it's now clean (no large base64 data)
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
                    logger.info(f"Image-to-video task submitted successfully with ID: {task_id}")
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