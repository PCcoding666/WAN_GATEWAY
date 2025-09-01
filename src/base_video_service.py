"""
Base Video Service for Shared Functionality.

This module provides the base class for all video generation services,
containing common functionality like polling, downloading, and error handling.
"""
import time
import logging
import os
import tempfile
from urllib.parse import urlparse
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseVideoService(ABC):
    """Base service class for video generation operations."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the base video service.
        
        Args:
            api_key: Optional API key override. If not provided, uses Config.DASHSCOPE_API_KEY
        """
        self.api_key = api_key or Config.DASHSCOPE_API_KEY
        
        if not self.api_key:
            raise ValueError("API key is required")
    
    @abstractmethod
    def get_api_endpoint(self) -> str:
        """Get the API endpoint for this service."""
        pass
    
    @abstractmethod
    def get_polling_interval(self) -> int:
        """Get the polling interval for this service."""
        pass
    
    @abstractmethod
    def get_max_poll_time(self) -> int:
        """Get the maximum polling time for this service."""
        pass
    
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
        polling_interval = self.get_polling_interval()
        max_poll_time = self.get_max_poll_time()
        
        while time.time() - start_time < max_poll_time:
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
                time.sleep(polling_interval)
                
            except Exception as e:
                logger.error(f"Error polling task {task_id}: {str(e)}")
                time.sleep(polling_interval)
        
        logger.error(f"Task {task_id} timed out after {max_poll_time} seconds")
        return None
    
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
    
    def _handle_api_error(self, response: requests.Response) -> str:
        """
        Handle API error responses and extract meaningful error messages.
        
        Args:
            response: The HTTP response object
            
        Returns:
            str: Formatted error message
        """
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
        return error_msg
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service status and configuration info.
        
        Returns:
            dict: Service status information
        """
        return {
            'api_configured': bool(self.api_key),
            'api_endpoint': self.get_api_endpoint(),
            'polling_interval': self.get_polling_interval(),
            'max_poll_time': self.get_max_poll_time(),
            'service_type': self.__class__.__name__
        }