[查看中文文档](API_zh.md)

# 📡 Wan Gateway API Documentation

This document provides detailed information about the API interfaces, data models, and integration guidelines for the Wan Gateway multi-modal video generator.

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Core Services](#core-services)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)

## 🔍 Overview

Wan Gateway provides three main video generation services:

1. **Text-to-Video** (`TextToVideoService`)
2. **Image-to-Video** (`ImageToVideoService`) 
3. **Keyframe-to-Video** (`KeyFrameVideoService`)

All services are managed through a unified factory pattern (`VideoServiceFactory`) and multi-modal application (`MultiModalVideoApp`).

## 🔐 Authentication

### API Key Configuration

```python
from src.config import Config

# API key configured through environment variables
DASHSCOPE_API_KEY = "your_api_key_here"

# Optional OSS configuration
OSS_ACCESS_KEY_ID = "your_oss_key_id"
OSS_ACCESS_KEY_SECRET = "your_oss_secret"
```

### Service Initialization

```python
from src.video_service_factory import MultiModalVideoApp

# Use default configuration
app = MultiModalVideoApp()

# Or specify API key
app = MultiModalVideoApp(api_key="your_api_key")
```

## ⚙️ Core Services

### 1. VideoServiceFactory

The service factory is responsible for creating appropriate service instances based on mode.

```python
from src.video_service_factory import VideoServiceFactory

# Get supported modes
modes = VideoServiceFactory.get_supported_modes()
# Returns: ["text_to_video", "image_to_video", "keyframe_to_video"]

# Create specific service
service = VideoServiceFactory.create_service("text_to_video", api_key)

# Get mode description
description = VideoServiceFactory.get_mode_description("text_to_video")

# Get available models
models = VideoServiceFactory.get_mode_models("text_to_video")

# Get default model
default_model = VideoServiceFactory.get_default_model("text_to_video")

# Validate mode and model compatibility
error = VideoServiceFactory.validate_mode_and_model("text_to_video", "wan2.2-t2v-plus")
```

### 2. MultiModalVideoApp

The multi-modal application provides a unified interface for handling all types of video generation.

```python
from src.video_service_factory import MultiModalVideoApp

app = MultiModalVideoApp()

# Generate video - text mode
result = app.generate_video(
    mode="text_to_video",
    prompt="A beautiful sunset scene",
    style="Cinematic",
    aspect_ratio="16:9",
    model="wan2.2-t2v-plus",
    negative_prompt="blurry, low quality",
    seed=42
)

# Generate video - image mode
result = app.generate_video(
    mode="image_to_video",
    image_file="/path/to/image.jpg",
    prompt="Add slow cloud movement",
    style="Realistic"
)

# Generate video - keyframe mode
result = app.generate_video(
    mode="keyframe_to_video",
    start_frame_file="/path/to/start.jpg",
    end_frame_file="/path/to/end.jpg",
    prompt="Smooth transformation process"
)

# Get service status
status = app.get_service_status()
```

### 3. TextToVideoService

Detailed API for text-to-video generation service.

```python
from src.text_to_video_service import TextToVideoService

service = TextToVideoService(api_key="your_api_key")

# Generate video
result = service.generate_video(
    prompt="Spectacular mountain sunrise",
    style="Cinematic",           # Optional style
    aspect_ratio="16:9",         # Aspect ratio
    model="wan2.2-t2v-plus",    # Model selection
    negative_prompt="blurry",    # Negative prompt
    seed=12345                   # Random seed
)

# Handle result
if result.success:
    print(f"Video URL: {result.video_url}")
    print(f"Local path: {result.local_video_path}")
    print(f"Generation time: {result.generation_time} seconds")
else:
    print(f"Generation failed: {result.error_message}")
```

### 4. ImageToVideoService

API for image-to-video generation service.

```python
from src.image_to_video_service import ImageToVideoService

service = ImageToVideoService(api_key="your_api_key")

# Generate video
result = service.generate_video(
    image_file="/path/to/input.jpg",  # Input image path
    prompt="Make flowers sway in wind",  # Optional guidance prompt
    style="Realistic",                # Style selection
    model="wan2.2-i2v-plus"          # Model selection
)
```

### 5. KeyFrameVideoService

API for keyframe-to-video generation service.

```python
from src.keyframe_to_video_service import KeyFrameVideoService

service = KeyFrameVideoService(api_key="your_api_key")

# Generate video
result = service.generate_video(
    start_frame_file="/path/to/start.jpg",  # Start frame
    end_frame_file="/path/to/end.jpg",      # End frame
    prompt="Slow and natural transition",   # Transition guidance
    style="Cinematic",                      # Style
    model="wanx2.1-kf2v-plus"              # Model
)
```

## 📊 Data Models

### VideoResult

Result object returned by all video generation services:

```python
@dataclass
class VideoResult:
    success: bool                    # Whether generation was successful
    video_url: Optional[str]         # Generated video URL
    local_video_path: Optional[str]  # Local video file path
    task_id: Optional[str]          # Task ID
    error_message: Optional[str]    # Error message
    generation_time: Optional[float] # Generation time (seconds)
    
    # Optional metadata
    model_used: Optional[str]       # Model used
    style_used: Optional[str]       # Style used
    aspect_ratio: Optional[str]     # Aspect ratio
```

### Configuration Models

```python
# Style options
STYLE_OPTIONS = [
    "<auto>",       # Auto
    "Cinematic",    # Cinematic
    "Anime",        # Anime
    "Realistic",    # Realistic
    "Abstract",     # Abstract
    "Documentary",  # Documentary
    "Commercial"    # Commercial
]

# Aspect ratio options
ASPECT_RATIO_OPTIONS = ["16:9", "1:1", "9:16"]

# Available models
MODEL_OPTIONS = {
    "wan2.2-t2v-plus": {
        "name": "wan2.2-t2v-plus",
        "description": "Latest model with enhanced detail and motion stability",
        "resolutions": ["480P", "1080P"],
        "api_type": "text_to_video"
    },
    "wan2.2-i2v-plus": {
        "name": "wan2.2-i2v-plus", 
        "description": "Latest image-to-video model",
        "resolutions": ["480P", "1080P"],
        "api_type": "image_to_video"
    }
    # ... more models
}
```

## ❌ Error Handling

### Common Error Types

```python
# Configuration errors
class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass

# API errors
class APIError(Exception):
    """API call errors"""
    pass

# Timeout errors
class TimeoutError(Exception):
    """Request timeout errors"""
    pass

# File errors
class FileProcessingError(Exception):
    """File processing errors"""
    pass
```

### Error Handling Example

```python
try:
    result = app.generate_video(
        mode="text_to_video",
        prompt="Test prompt"
    )
    if not result.success:
        print(f"Generation failed: {result.error_message}")
        
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except APIError as e:
    print(f"API error: {e}")
except TimeoutError as e:
    print(f"Timeout error: {e}")
except Exception as e:
    print(f"Unknown error: {e}")
```

## 💡 Usage Examples

### Basic Text-to-Video Generation

```python
from src.video_service_factory import MultiModalVideoApp

def generate_simple_video():
    app = MultiModalVideoApp()
    
    result = app.generate_video(
        mode="text_to_video",
        prompt="A cute kitten playing in a garden"
    )
    
    if result.success:
        print(f"✅ Video generated successfully!")
        print(f"📹 Video URL: {result.video_url}")
        if result.local_video_path:
            print(f"📁 Local path: {result.local_video_path}")
    else:
        print(f"❌ Generation failed: {result.error_message}")

generate_simple_video()
```

### Advanced Configuration Generation

```python
def generate_advanced_video():
    app = MultiModalVideoApp()
    
    result = app.generate_video(
        mode="text_to_video",
        prompt="Futuristic cityscape with neon lights flashing",
        style="Cinematic",
        aspect_ratio="16:9", 
        model="wan2.2-t2v-plus",
        negative_prompt="blurry, noise, low quality",
        seed=42  # Ensure reproducibility
    )
    
    return result
```

### Image-to-Video Generation

```python
def image_to_video_example():
    app = MultiModalVideoApp()
    
    result = app.generate_video(
        mode="image_to_video",
        image_file="/path/to/beautiful_landscape.jpg",
        prompt="Add slowly moving clouds and grass swaying in breeze",
        style="Realistic"
    )
    
    return result
```

### Keyframe-to-Video Generation

```python
def keyframe_to_video_example():
    app = MultiModalVideoApp()
    
    result = app.generate_video(
        mode="keyframe_to_video", 
        start_frame_file="/path/to/day_scene.jpg",
        end_frame_file="/path/to/night_scene.jpg",
        prompt="Natural transition from day to night"
    )
    
    return result
```

### Batch Generation

```python
def batch_generation():
    app = MultiModalVideoApp()
    
    prompts = [
        "Cherry blossoms falling in spring",
        "Ocean waves on a summer beach",
        "Autumn leaves falling gently",
        "Snowflakes dancing in winter"
    ]
    
    results = []
    for prompt in prompts:
        result = app.generate_video(
            mode="text_to_video",
            prompt=prompt,
            style="Cinematic"
        )
        results.append(result)
        
        if result.success:
            print(f"✅ '{prompt}' generated successfully")
        else:
            print(f"❌ '{prompt}' generation failed: {result.error_message}")
    
    return results
```

## 🎯 Best Practices

### 1. Performance Optimization

```python
# Use appropriate polling intervals
# Text generation: 2-second intervals
# Image/keyframe generation: 30-second intervals

# Set reasonable timeouts
# Text generation: 5 minutes
# Image/keyframe generation: 15 minutes

# Reuse service instances
app = MultiModalVideoApp()  # Create once, use multiple times
```

### 2. Error Retry Mechanism

```python
import time
import random

def generate_with_retry(app, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            result = app.generate_video(**kwargs)
            if result.success:
                return result
            
            # If API error, wait and retry
            if "rate limit" in result.error_message.lower():
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)
    
    return None
```

### 3. Resource Management

```python
def safe_generation(app, **kwargs):
    try:
        # Check API quota
        status = app.get_service_status()
        if not status['api_configured']:
            raise ConfigurationError("API not properly configured")
        
        # Generate video
        result = app.generate_video(**kwargs)
        
        # Clean up temporary files
        if result.success and result.local_video_path:
            # Can optionally delete local files after processing
            # os.remove(result.local_video_path)
            pass
            
        return result
        
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise
```

### 4. Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def logged_generation(app, **kwargs):
    logger.info(f"Starting video generation: {kwargs}")
    
    start_time = time.time()
    result = app.generate_video(**kwargs)
    end_time = time.time()
    
    if result.success:
        logger.info(f"Video generation successful, took: {end_time - start_time:.2f} seconds")
    else:
        logger.error(f"Video generation failed: {result.error_message}")
    
    return result
```

## 📚 Additional Resources

- [Main Documentation](README.md) - Project overview and quick start
- [Deployment Guide](DEPLOYMENT.md) - Detailed deployment instructions
- [Configuration Documentation](src/config.py) - Complete configuration options
- [Example Code](demo.py) - Feature demonstration script
For Chinese documentation, see the [doc](doc/) folder.

---

**Need help?** Please check the project's Issues page or submit a new issue.