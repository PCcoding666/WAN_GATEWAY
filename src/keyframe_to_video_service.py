"""
KeyFrame-to-Video Service for Bailian API Integration.

This module provides the service for generating videos from start and end frame images
using Alibaba's Bailian wan-kf2v API.
"""
import json
import time
import logging
import base64
from typing import Optional, Tuple
from PIL import Image
import requests
from .config import Config
from .base_video_service import BaseVideoService
from .text_to_video_service import VideoResult

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
            
            # Process both images
            start_base64, start_info = self._process_image_upload(start_frame_file, "start")
            end_base64, end_info = self._process_image_upload(end_frame_file, "end")
            
            if not start_base64 or not end_base64:
                return VideoResult(
                    success=False,
                    error_message="Failed to process one or both uploaded images"
                )
            
            # Build request payload
            request_data = self._build_keyframe_request(
                first_frame_base64=start_base64,
                last_frame_base64=end_base64,
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
        Process uploaded image and convert to base64.
        
        Args:
            image_file: The uploaded image file from Gradio
            frame_type: "start" or "end" for logging purposes
            
        Returns:
            tuple: (base64_string, image_info) or (None, None) if failed
        """
        try:
            # Open and validate the image
            with Image.open(image_file) as img:
                # Get image info
                width, height = img.size
                format = img.format or 'JPEG'
                file_size_mb = image_file.size / (1024 * 1024) if hasattr(image_file, 'size') else 0
                
                # Validate image dimensions and format
                validation_error = Config.validate_image_upload(file_size_mb, format, width, height)
                if validation_error:
                    logger.error(f"{frame_type.capitalize()} frame validation failed: {validation_error}")
                    return None, None
                
                # Convert to RGB if needed (for JPEG compatibility)
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                
                # Convert to base64 (just the base64 string, not data URI)
                import io
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=95)
                image_bytes = buffer.getvalue()
                base64_string = base64.b64encode(image_bytes).decode('utf-8')
                
                image_info = {
                    "width": width,
                    "height": height,
                    "format": format,
                    "file_size_mb": file_size_mb,
                    "frame_type": frame_type
                }
                
                logger.info(f"{frame_type.capitalize()} frame processed successfully: {width}x{height}, {format}, {file_size_mb:.2f}MB")
                return base64_string, image_info
                
        except Exception as e:
            logger.error(f"Error processing {frame_type} frame: {str(e)}")
            return None, None
    
    def _build_keyframe_request(
        self,
        first_frame_base64: str,
        last_frame_base64: str,
        prompt: Optional[str] = None,
        model: str = "wanx2.1-kf2v-plus"
    ) -> dict:
        """
        Build API request payload for keyframe-to-video generation.
        
        Returns:
            dict: Formatted request payload
        """
        request_data = {
            "model": model,
            "input": {
                "first_frame_url": first_frame_base64,
                "last_frame_url": last_frame_base64
            },
            "parameters": {
                "resolution": "720P"  # Fixed for keyframe models
            }
        }
        
        # Add optional prompt
        if prompt and prompt.strip():
            request_data["input"]["prompt"] = prompt.strip()
        
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
            # Don't log the full request payload as it contains large base64 data
            log_data = request_data.copy()
            if 'input' in log_data:
                if 'first_frame_url' in log_data['input']:
                    log_data['input']['first_frame_url'] = f"[base64 data: {len(log_data['input']['first_frame_url'])} chars]"
                if 'last_frame_url' in log_data['input']:
                    log_data['input']['last_frame_url'] = f"[base64 data: {len(log_data['input']['last_frame_url'])} chars]"
            logger.info(f"Request payload (truncated): {json.dumps(log_data, indent=2)}")
            
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