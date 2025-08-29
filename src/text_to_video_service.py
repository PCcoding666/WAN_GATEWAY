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

class TextToVideoService:
    """Service for generating videos from text using Bailian API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TextToVideoService.
        
        Args:
            api_key: Optional API key override. If not provided, uses Config.DASHSCOPE_API_KEY
        """
        self.api_key = api_key or Config.DASHSCOPE_API_KEY
        self.base_url = Config.API_ENDPOINT
        
        if not self.api_key:
            raise ValueError("API key is required")
    
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
                    generation_time=generation_time
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
        
        if model not in Config.MODEL_OPTIONS:
            return f"Invalid model. Must be one of: {', '.join(Config.MODEL_OPTIONS.keys())}"
        
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
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg = error_data['message']
                    elif 'error' in error_data:
                        error_msg = error_data['error']
                    elif 'code' in error_data and 'message' in error_data:
                        error_msg = f"{error_data['code']}: {error_data['message']}"
                except:
                    error_msg += f": {response.text}"
                
                logger.error(f"API request failed: {error_msg}")
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
    
    def _poll_task_result(self, task_id: str) -> Optional[str]:
        """
        Poll for task completion and retrieve video URL.
        
        Args:
            task_id: Task ID to poll for
            
        Returns:
            Optional[str]: Video URL if successful, None if failed or timed out
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # Use the correct polling endpoint
        poll_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        start_time = time.time()
        
        while time.time() - start_time < Config.MAX_POLL_TIME:
            try:
                response = requests.get(
                    poll_url,
                    headers=headers,
                    timeout=Config.REQUEST_TIMEOUT
                )
                
                logger.info(f"Polling response status: {response.status_code}")
                logger.info(f"Polling response content: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check task status
                    if 'output' in result:
                        status = result['output'].get('task_status', 'UNKNOWN')
                        
                        if status == 'SUCCEEDED':
                            # Extract video URL
                            if 'video_url' in result['output']:
                                return result['output']['video_url']
                            elif 'results' in result['output'] and result['output']['results']:
                                # Alternative response format
                                video_result = result['output']['results'][0]
                                if 'url' in video_result:
                                    return video_result['url']
                        elif status == 'FAILED':
                            logger.error(f"Task {task_id} failed")
                            if 'error' in result['output']:
                                logger.error(f"Error details: {result['output']['error']}")
                            return None
                        elif status in ['PENDING', 'RUNNING']:
                            # Continue polling
                            logger.info(f"Task {task_id} status: {status}, continuing to poll...")
                        else:
                            logger.warning(f"Unknown task status: {status}")
                else:
                    logger.error(f"Polling failed with status {response.status_code}: {response.text}")
                
                # Wait before next poll
                time.sleep(Config.POLLING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error polling task {task_id}: {str(e)}")
                time.sleep(Config.POLLING_INTERVAL)
        
        logger.error(f"Task {task_id} timed out after {Config.MAX_POLL_TIME} seconds")
        return None
    
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
    
    def _download_video_locally(self, video_url: str, task_id: str) -> Optional[str]:
        """
        Download video from OSS URL to local temporary file with retry logic.
        
        Args:
            video_url: Remote video URL from OSS
            task_id: Task ID for unique filename
            
        Returns:
            Optional[str]: Local file path if successful, None if failed
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading video (attempt {attempt + 1}/{max_retries}) from: {video_url[:100]}...")
                
                # Create a unique filename
                parsed_url = urlparse(video_url)
                file_extension = os.path.splitext(parsed_url.path)[1] or '.mp4'
                
                # Create temporary directory if it doesn't exist
                temp_dir = os.path.join(tempfile.gettempdir(), 'wan_gateway_videos')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Create local file path
                local_filename = f"video_{task_id}_{int(time.time())}{file_extension}"
                local_path = os.path.join(temp_dir, local_filename)
                
                # Download the video with comprehensive headers and session
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'video',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'cross-site'
                })
                
                # Configure adapters for better connection handling
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry
                
                retry_strategy = Retry(
                    total=3,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["HEAD", "GET", "OPTIONS"]
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                
                # Download with streaming and longer timeout
                response = session.get(
                    video_url,
                    stream=True,
                    timeout=(30, 120),  # (connect_timeout, read_timeout)
                    verify=True
                )
                
                if response.status_code == 200:
                    # Write video to local file with progress tracking
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=16384):  # Larger chunks for video
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # Log progress for large files
                                if total_size > 0 and downloaded_size % (1024 * 1024) == 0:  # Every MB
                                    progress = (downloaded_size / total_size) * 100
                                    logger.info(f"Download progress: {progress:.1f}%")
                    
                    file_size = os.path.getsize(local_path)
                    if file_size > 0:
                        logger.info(f"Video downloaded successfully to: {local_path} (Size: {file_size} bytes)")
                        return local_path
                    else:
                        logger.error("Downloaded file is empty")
                        os.unlink(local_path)  # Remove empty file
                        
                elif response.status_code == 403:
                    logger.error(f"Access denied (403) - URL may have expired: {video_url}")
                    break  # Don't retry on permission errors
                elif response.status_code == 404:
                    logger.error(f"Video not found (404): {video_url}")
                    break  # Don't retry on not found errors
                else:
                    logger.error(f"Failed to download video: HTTP {response.status_code} - {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Download attempt {attempt + 1} timed out")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        logger.error(f"Failed to download video after {max_retries} attempts")
        return None
    
    def get_service_status(self) -> dict:
        """
        Get service status and configuration info.
        
        Returns:
            dict: Service status information
        """
        return {
            'api_configured': bool(self.api_key),
            'api_endpoint': self.base_url,
            'max_poll_time': Config.MAX_POLL_TIME,
            'polling_interval': Config.POLLING_INTERVAL,
            'supported_styles': Config.STYLE_OPTIONS,
            'supported_ratios': Config.ASPECT_RATIO_OPTIONS,
            'available_models': list(Config.MODEL_OPTIONS.keys()),
            'default_model': Config.DEFAULT_MODEL
        }