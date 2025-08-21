"""
Utility functions for the Gradio Bailian Text-to-Video Application.

This module provides helper functions and utilities used across the application.
"""
import re
import hashlib
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def sanitize_prompt(prompt: str) -> str:
    """
    Sanitize user prompt for safe processing.
    
    Args:
        prompt: Raw user prompt
        
    Returns:
        str: Sanitized prompt
    """
    if not prompt:
        return ""
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', prompt.strip())
    
    # Remove potentially harmful characters but keep basic punctuation
    cleaned = re.sub(r'[^\w\s\.,!?;:\-\(\)\'\"]+', '', cleaned)
    
    return cleaned

def generate_request_id(prompt: str, style: str, aspect_ratio: str) -> str:
    """
    Generate a unique request ID for tracking purposes.
    
    Args:
        prompt: Video description
        style: Selected style
        aspect_ratio: Selected aspect ratio
        
    Returns:
        str: Unique request ID
    """
    content = f"{prompt}_{style}_{aspect_ratio}".encode('utf-8')
    return hashlib.md5(content).hexdigest()[:12]

def format_duration(seconds: float) -> str:
    """
    Format duration in a human-readable way.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to specified length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def validate_seed(seed_value: Any) -> Optional[int]:
    """
    Validate and convert seed value.
    
    Args:
        seed_value: Raw seed value from UI
        
    Returns:
        Optional[int]: Valid integer seed or None
    """
    if seed_value is None or seed_value == "":
        return None
    
    try:
        seed_int = int(float(seed_value))
        # Ensure seed is in reasonable range
        if -2147483648 <= seed_int <= 2147483647:
            return seed_int
        else:
            logger.warning(f"Seed value {seed_int} out of range, ignoring")
            return None
    except (ValueError, TypeError):
        logger.warning(f"Invalid seed value: {seed_value}")
        return None

def get_error_message(error: Exception) -> str:
    """
    Get user-friendly error message.
    
    Args:
        error: Exception object
        
    Returns:
        str: User-friendly error message
    """
    error_str = str(error).lower()
    
    if "timeout" in error_str:
        return "Request timed out. Please try again."
    elif "connection" in error_str:
        return "Connection error. Please check your internet connection."
    elif "authentication" in error_str or "api key" in error_str:
        return "Authentication failed. Please check your API key."
    elif "rate limit" in error_str:
        return "Rate limit exceeded. Please wait a moment before trying again."
    elif "quota" in error_str:
        return "API quota exceeded. Please check your account limits."
    else:
        return f"An error occurred: {str(error)}"

def log_request(
    prompt: str, 
    style: str, 
    aspect_ratio: str, 
    request_id: str,
    success: bool = None,
    duration: float = None
) -> None:
    """
    Log request information for monitoring and debugging.
    
    Args:
        prompt: Video description
        style: Selected style
        aspect_ratio: Selected aspect ratio
        request_id: Unique request ID
        success: Whether request was successful
        duration: Request duration in seconds
    """
    truncated_prompt = truncate_text(prompt, 100)
    
    log_data = {
        'request_id': request_id,
        'prompt': truncated_prompt,
        'style': style,
        'aspect_ratio': aspect_ratio
    }
    
    if success is not None:
        log_data['success'] = success
    if duration is not None:
        log_data['duration'] = f"{duration:.2f}s"
    
    logger.info(f"Request: {log_data}")

class RequestCache:
    """Simple in-memory cache for request results."""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            # Move to end for LRU
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if key in self.cache:
            # Update existing
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # Remove oldest
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        self.cache[key] = value
        self.access_order.append(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()

# Global cache instance
request_cache = RequestCache()