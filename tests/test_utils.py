"""
Unit tests for utility functions.
"""
import pytest
from src.utils import (
    validate_url, sanitize_prompt, generate_request_id,
    format_duration, truncate_text, validate_seed,
    get_error_message, RequestCache
)

class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_validate_url_valid_https(self):
        """Test URL validation with valid HTTPS URL."""
        assert validate_url("https://example.com/video.mp4") is True
    
    def test_validate_url_valid_http(self):
        """Test URL validation with valid HTTP URL."""
        assert validate_url("http://example.com/video.mp4") is True
    
    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "",
            "example.com",
            "://missing-scheme"
        ]
        
        for url in invalid_urls:
            assert validate_url(url) is False
    
    def test_sanitize_prompt_basic(self):
        """Test basic prompt sanitization."""
        prompt = "  A beautiful sunset over mountains  "
        result = sanitize_prompt(prompt)
        assert result == "A beautiful sunset over mountains"
    
    def test_sanitize_prompt_excessive_whitespace(self):
        """Test sanitization with excessive whitespace."""
        prompt = "A    beautiful     sunset"
        result = sanitize_prompt(prompt)
        assert result == "A beautiful sunset"
    
    def test_sanitize_prompt_special_characters(self):
        """Test sanitization with special characters."""
        prompt = "A beautiful sunset!!! @#$%^&*"
        result = sanitize_prompt(prompt)
        # Should keep basic punctuation but remove harmful characters
        assert "beautiful sunset" in result
        assert "@" not in result
        assert "#" not in result
    
    def test_sanitize_prompt_empty(self):
        """Test sanitization with empty prompt."""
        assert sanitize_prompt("") == ""
        assert sanitize_prompt(None) == ""
    
    def test_generate_request_id_consistent(self):
        """Test that request ID generation is consistent."""
        prompt = "Test prompt"
        style = "Cinematic"
        aspect_ratio = "16:9"
        
        id1 = generate_request_id(prompt, style, aspect_ratio)
        id2 = generate_request_id(prompt, style, aspect_ratio)
        
        assert id1 == id2
        assert len(id1) == 12  # MD5 hash truncated to 12 chars
    
    def test_generate_request_id_different_inputs(self):
        """Test that different inputs generate different IDs."""
        id1 = generate_request_id("Prompt 1", "Cinematic", "16:9")
        id2 = generate_request_id("Prompt 2", "Cinematic", "16:9")
        
        assert id1 != id2
    
    def test_format_duration_seconds(self):
        """Test duration formatting for seconds."""
        assert format_duration(5.5) == "5.5s"
        assert format_duration(30.0) == "30.0s"
        assert format_duration(59.9) == "59.9s"
    
    def test_format_duration_minutes(self):
        """Test duration formatting for minutes."""
        assert format_duration(60) == "1m 0s"
        assert format_duration(125) == "2m 5s"
        assert format_duration(3599) == "59m 59s"
    
    def test_format_duration_hours(self):
        """Test duration formatting for hours."""
        assert format_duration(3600) == "1h 0m"
        assert format_duration(7265) == "2h 1m"
    
    def test_truncate_text_no_truncation(self):
        """Test text truncation when text is shorter than limit."""
        text = "Short text"
        result = truncate_text(text, 50)
        assert result == text
    
    def test_truncate_text_with_truncation(self):
        """Test text truncation when text exceeds limit."""
        text = "This is a very long text that should be truncated"
        result = truncate_text(text, 20)
        assert len(result) == 20
        assert result.endswith("...")
        assert "This is a very" in result
    
    def test_validate_seed_valid_integer(self):
        """Test seed validation with valid integers."""
        assert validate_seed(42) == 42
        assert validate_seed("123") == 123
        assert validate_seed(0) == 0
        assert validate_seed(-100) == -100
    
    def test_validate_seed_valid_float(self):
        """Test seed validation with float that converts to int."""
        assert validate_seed(42.0) == 42
        assert validate_seed("123.0") == 123
    
    def test_validate_seed_invalid(self):
        """Test seed validation with invalid values."""
        invalid_seeds = [
            "not-a-number",
            "",
            None,
            "abc123",
            []
        ]
        
        for seed in invalid_seeds:
            assert validate_seed(seed) is None
    
    def test_validate_seed_out_of_range(self):
        """Test seed validation with out-of-range values."""
        # Test values outside 32-bit integer range
        assert validate_seed(2**32) is None
        assert validate_seed(-2**32) is None
    
    def test_get_error_message_timeout(self):
        """Test error message for timeout errors."""
        error = Exception("Connection timeout occurred")
        message = get_error_message(error)
        assert "timed out" in message.lower()
    
    def test_get_error_message_connection(self):
        """Test error message for connection errors."""
        error = Exception("Connection failed")
        message = get_error_message(error)
        assert "connection" in message.lower()
    
    def test_get_error_message_authentication(self):
        """Test error message for authentication errors."""
        error = Exception("API key authentication failed")
        message = get_error_message(error)
        assert "authentication" in message.lower()
    
    def test_get_error_message_rate_limit(self):
        """Test error message for rate limit errors."""
        error = Exception("Rate limit exceeded")
        message = get_error_message(error)
        assert "rate limit" in message.lower()
    
    def test_get_error_message_generic(self):
        """Test error message for generic errors."""
        error = Exception("Some random error")
        message = get_error_message(error)
        assert "Some random error" in message

class TestRequestCache:
    """Test cases for RequestCache class."""
    
    def test_cache_get_set(self):
        """Test basic cache get/set operations."""
        cache = RequestCache(max_size=5)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_cache_get_nonexistent(self):
        """Test getting non-existent key returns None."""
        cache = RequestCache()
        assert cache.get("nonexistent") is None
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = RequestCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_cache_access_updates_order(self):
        """Test that accessing a key updates its position in LRU order."""
        cache = RequestCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key1 to move it to end
        cache.get("key1")
        
        # Add key3, should evict key2 (not key1)
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
    
    def test_cache_update_existing(self):
        """Test updating existing cache entry."""
        cache = RequestCache()
        
        cache.set("key1", "value1")
        cache.set("key1", "value2")  # Update existing
        
        assert cache.get("key1") == "value2"
    
    def test_cache_clear(self):
        """Test clearing the cache."""
        cache = RequestCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert len(cache.cache) == 0
        assert len(cache.access_order) == 0