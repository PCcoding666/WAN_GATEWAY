"""
Unit tests for the configuration module.
"""
import pytest
import os
from unittest.mock import patch

from src.config import Config

class TestConfig:
    """Test cases for Config class."""
    
    def test_style_options_not_empty(self):
        """Test that style options are not empty."""
        assert len(Config.STYLE_OPTIONS) > 0
        assert isinstance(Config.STYLE_OPTIONS, list)
    
    def test_style_options_contains_auto(self):
        """Test that style options contain auto option."""
        assert "<auto>" in Config.STYLE_OPTIONS
    
    def test_aspect_ratio_options_not_empty(self):
        """Test that aspect ratio options are not empty."""
        assert len(Config.ASPECT_RATIO_OPTIONS) > 0
        assert isinstance(Config.ASPECT_RATIO_OPTIONS, list)
    
    def test_aspect_ratio_options_contain_standard_ratios(self):
        """Test that aspect ratio options contain standard ratios."""
        expected_ratios = ["16:9", "1:1", "9:16"]
        for ratio in expected_ratios:
            assert ratio in Config.ASPECT_RATIO_OPTIONS
    
    def test_api_settings_are_reasonable(self):
        """Test that API settings have reasonable values."""
        assert Config.MAX_RETRIES >= 1
        assert Config.POLLING_INTERVAL > 0
        assert Config.REQUEST_TIMEOUT > 0
        assert Config.MAX_POLL_TIME > Config.POLLING_INTERVAL
    
    def test_ui_settings_are_reasonable(self):
        """Test that UI settings have reasonable values."""
        assert Config.MAX_PROMPT_LENGTH > 0
        assert Config.DEFAULT_STYLE in Config.STYLE_OPTIONS
        assert Config.DEFAULT_ASPECT_RATIO in Config.ASPECT_RATIO_OPTIONS
    
    @patch.dict(os.environ, {'DASHSCOPE_API_KEY': 'test-key'})
    def test_validate_config_success(self):
        """Test successful config validation."""
        with patch.object(Config, 'DASHSCOPE_API_KEY', 'test-key'):
            assert Config.validate_config() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_config_missing_api_key(self):
        """Test config validation with missing API key."""
        with patch.object(Config, 'DASHSCOPE_API_KEY', None):
            with pytest.raises(ValueError, match="DASHSCOPE_API_KEY"):
                Config.validate_config()
    
    def test_get_style_display_name_auto(self):
        """Test display name for auto style."""
        display_name = Config.get_style_display_name("<auto>")
        assert "Auto" in display_name
        assert "Recommended" in display_name
    
    def test_get_style_display_name_regular(self):
        """Test display name for regular style."""
        style = "Cinematic"
        display_name = Config.get_style_display_name(style)
        assert display_name == style
    
    def test_get_aspect_ratio_display_name(self):
        """Test display names for aspect ratios."""
        test_cases = {
            "16:9": "Widescreen",
            "1:1": "Square", 
            "9:16": "Portrait"
        }
        
        for ratio, expected_word in test_cases.items():
            display_name = Config.get_aspect_ratio_display_name(ratio)
            assert expected_word in display_name
            assert ratio in display_name
    
    def test_get_aspect_ratio_display_name_unknown(self):
        """Test display name for unknown aspect ratio."""
        unknown_ratio = "4:3"
        display_name = Config.get_aspect_ratio_display_name(unknown_ratio)
        assert display_name == unknown_ratio