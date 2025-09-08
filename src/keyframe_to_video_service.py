"""
KeyFrame-to-Video Service for Bailian API Integration.

This module provides the service for generating videos from start and end frame images
using Alibaba's Bailian wan-kf2v API.
"""
import json
import time
import logging
# import base64  # No longer needed - using OSS URLs
from typing import Optional, Tuple
from PIL import Image
import requests
from .config import Config
from .base_video_service import BaseVideoService
from .text_to_video_service import VideoResult
from .oss_service import oss_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeyFrameVideoService(BaseVideoService):
    """Service for generating videos from start and end frame images using Bailian API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the KeyFrameVideoService.
        
        Args:
            api_key: Optional API key override. If not provided, uses Config.DASHSCOPE_API_KEY
        """
        super().__init__(api_key)
        self.base_url = Config.KEYFRAME_VIDEO_ENDPOINT
    
    def get_api_endpoint(self) -> str:
        """Get the API endpoint for keyframe-to-video generation."""
        return self.base_url
    
    def get_polling_interval(self) -> int:
        """Get the polling interval for keyframe-to-video generation."""
        return Config.KEYFRAME_POLLING_INTERVAL
    
    def get_max_poll_time(self) -> int:
        """Get the maximum polling time for keyframe-to-video generation."""
        return Config.KEYFRAME_MAX_POLL_TIME
    
    def generate_video(
        self,
        start_frame_file,
        end_frame_file,
        prompt: str = "",
        style: str = Config.DEFAULT_STYLE,
        model: str = "wanx2.1-kf2v-plus"
    ) -> VideoResult:
        """
        Generate video from start and end frame images.
        
        Args:
            start_frame_file: The uploaded start frame image file (from Gradio)
            end_frame_file: The uploaded end frame image file (from Gradio)
            prompt: Optional text prompt for guidance
            style: Video style (default from config)
            model: Model to use for generation (must be keyframe model)
            
        Returns:
            VideoResult with success status and video URL or error message
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            validation_error = self._validate_keyframe_inputs(start_frame_file, end_frame_file, prompt, model)
            if validation_error:
                return VideoResult(
                    success=False,
                    error_message=validation_error
                )
            
            # Process both images and upload to OSS
            start_public_url, start_info = self._process_image_upload(start_frame_file, "start")
            end_public_url, end_info = self._process_image_upload(end_frame_file, "end")
            
            if not start_public_url or not end_public_url:
                return VideoResult(
                    success=False,
                    error_message="Failed to process and upload one or both images to OSS"
                )
            
            # Build request payload
            request_data = self._build_keyframe_request(
                first_frame_url=start_public_url,
                last_frame_url=end_public_url,
                prompt=prompt.strip() if prompt else None,
                model=model
            )
            
            logger.info(f"Initiating keyframe-to-video generation...")
            
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
                    generation_mode="keyframe_to_video",
                    model_used=model,
                    input_metadata={
                        "prompt": prompt,
                        "style": style,
                        "start_frame_info": start_info,
                        "end_frame_info": end_info
                    }
                )
            else:
                return VideoResult(
                    success=False,
                    error_message="Video generation failed or timed out",
                    task_id=task_id
                )
                
        except Exception as e:
            logger.error(f"Keyframe-to-video generation error: {str(e)}")
            return VideoResult(
                success=False,
                error_message=f"Generation failed: {str(e)}"
            )
    
    def _validate_keyframe_inputs(
        self,
        start_frame_file,
        end_frame_file,
        prompt: str,
        model: str
    ) -> Optional[str]:
        """
        Validate input parameters for keyframe-to-video generation.
        
        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        if start_frame_file is None:
            return "Start frame image is required"
        
        if end_frame_file is None:
            return "End frame image is required"
        
        if model not in Config.get_keyframe_to_video_models():
            return f"Invalid model for keyframe-to-video. Must be one of: {', '.join(Config.get_keyframe_to_video_models())}"
        
        if prompt and len(prompt.strip()) > Config.MAX_PROMPT_LENGTH:
            return f"Prompt too long. Maximum {Config.MAX_PROMPT_LENGTH} characters allowed"
        
        return None
    
    def _process_image_upload(self, image_file, frame_type: str) -> Tuple[Optional[str], Optional[dict]]:
        """
        Process uploaded image and upload to OSS to get public URL.
        
        Args:
            image_file: The uploaded image file from Gradio
            frame_type: "start" or "end" for logging purposes
            
        Returns:
            tuple: (public_url, image_info) or (None, None) if failed
        """
        try:
            # Validate image file
            if image_file is None:
                logger.error(f"No {frame_type} frame image file provided")
                return None, None
            
            # Get basic image info for validation
            with Image.open(image_file) as img:
                width, height = img.size
                original_format = img.format or 'JPEG'
                file_size_mb = image_file.size / (1024 * 1024) if hasattr(image_file, 'size') else 0
                
                # Validate image dimensions and format
                validation_error = Config.validate_image_upload(file_size_mb, original_format, width, height)
                if validation_error:
                    logger.error(f"{frame_type.title()} frame validation failed: {validation_error}")
                    return None, None
            
            # Upload to OSS and get public URL
            public_url, upload_info = oss_service.upload_image(image_file)
            
            if public_url:
                logger.info(f"{frame_type.title()} frame uploaded successfully to OSS: {public_url[:80]}...")
                
                # Combine validation info with upload info
                image_info = {
                    "public_url": public_url,
                    "original_width": width,
                    "original_height": height,
                    "original_format": original_format,
                    "file_size_mb": file_size_mb,
                    "frame_type": frame_type,
                    **upload_info
                }
                
                return public_url, image_info
            else:
                logger.error(f"Failed to upload {frame_type} frame to OSS")
                return None, None
                
        except Exception as e:
            logger.error(f"Error processing {frame_type} frame upload: {str(e)}")
            return None, None
    
    def _build_keyframe_request(
        self,
        first_frame_url: str,
        last_frame_url: str,
        prompt: Optional[str] = None,
        model: str = "wanx2.1-kf2v-plus"
    ) -> dict:
        """
        Build API request payload for keyframe-to-video generation using public URLs.
        
        Args:
            first_frame_url: Public URL of the first frame image
            last_frame_url: Public URL of the last frame image
            prompt: Optional text prompt
            model: Model to use for generation
            
        Returns:
            dict: Formatted request payload
        """
        request_data = {
            "model": model,
            "input": {
                "first_frame_url": first_frame_url,
                "last_frame_url": last_frame_url
            },
            "parameters": {
                "resolution": "720P",  # Fixed for keyframe models
                "prompt_extend": True  # Enable prompt extension for better results
            }
        }
        
        # Add optional prompt
        if prompt and prompt.strip():
            request_data["input"]["prompt"] = prompt.strip()
        
        logger.info(f"Using model: {model}, resolution: 720P")
        logger.info(f"First frame URL: {first_frame_url[:80]}...")
        logger.info(f"Last frame URL: {last_frame_url[:80]}...")
        
        return request_data
    
    def _submit_task(self, request_data: dict) -> dict:
        """
        Submit keyframe-to-video generation task to API.
        
        Returns:
            dict: Response containing task_id or error information
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-DashScope-Async': 'enable'
        }
        
        try:
            logger.info(f"Submitting keyframe-to-video task to: {self.base_url}")
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
                    logger.info(f"Keyframe-to-video task submitted successfully with ID: {task_id}")
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