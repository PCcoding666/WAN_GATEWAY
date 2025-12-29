import pytest
from src.config import Config

class TestConfig:
    def test_validate_config_success(self, mock_env_vars):
        """Test configuration validation with valid environment."""
        assert Config.validate_config() is True

    def test_validate_config_missing_api_key(self, monkeypatch):
        """Test configuration validation with missing API key."""
        monkeypatch.setattr(Config, 'DASHSCOPE_API_KEY', None)
        with pytest.raises(ValueError, match="DASHSCOPE_API_KEY environment variable is required"):
            Config.validate_config()

    def test_get_style_display_name(self):
        """Test style display name retrieval."""
        assert Config.get_style_display_name("<auto>") == "Auto (Recommended)"
        assert Config.get_style_display_name("Cinematic") == "Cinematic"

    def test_get_model_display_name(self):
        """Test model display name retrieval."""
        model_id = "wan2.2-t2v-plus"
        assert Config.get_model_display_name(model_id) == "wan2.2-t2v-plus"
        assert Config.get_model_display_name("unknown-model") == "unknown-model"

    def test_supports_audio(self):
        """Test audio support check."""
        assert Config.supports_audio("wan2.5-t2v-preview") is True
        assert Config.supports_audio("wan2.2-t2v-plus") is False

    def test_validate_image_upload(self):
        """Test image upload validation."""
        # Valid case
        assert Config.validate_image_upload(5, "JPG", 1000, 1000) is None
        
        # Invalid size
        assert Config.validate_image_upload(15, "JPG", 1000, 1000) is not None
        
        # Invalid format
        assert Config.validate_image_upload(5, "GIF", 1000, 1000) is not None
        
        # Invalid dimensions (too small)
        assert Config.validate_image_upload(5, "JPG", 100, 100) is not None
        
        # Invalid dimensions (too large)
        assert Config.validate_image_upload(5, "JPG", 3000, 3000) is not None
