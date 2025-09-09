# 🎬 Wan Gateway - Multi-Modal Video Generator

A comprehensive web application built with Gradio that provides an intuitive interface for generating videos using Alibaba's Bailian APIs. Supports three generation modes: text-to-video, image-to-video, and keyframe-to-video generation.

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://python.org)
[![Gradio](https://img.shields.io/badge/gradio-5.43.1%2B-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Core Features

- **🎥 Text-to-Video**: Convert text descriptions into high-quality videos
- **🖼️ Image-to-Video**: Generate dynamic videos from a single image
- **🎞️ Keyframe-to-Video**: Create smooth transitions between start and end frames
- **🎨 Multiple Style Options**: Support for cinematic, anime, realistic, and other artistic styles
- **📐 Flexible Aspect Ratios**: Support for 16:9, 1:1, 9:16 and other ratios
- **⚙️ Advanced Settings**: Support for negative prompts, seed control, and fine-tuning
- **🤖 Smart Model Selection**: Automatically choose optimal models based on generation mode
- **📱 Responsive Interface**: Beautiful and user-friendly interface with real-time feedback
- **📊 Status Tracking**: Detailed progress and error reporting
- **☁️ OSS Integration**: Optional Alibaba Cloud OSS storage support

## 🚀 Quick Start

### Requirements

- Python 3.13 or higher
- Valid Alibaba Bailian API key
- Stable internet connection

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PCcoding666/WAN_GATEWAY.git
   cd Wan_Gateway
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Copy `.env.example` to `.env` and fill in the configuration:
   ```bash
   cp .env.example .env
   # Edit .env file and enter your API key
   DASHSCOPE_API_KEY=your_api_key_here
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

5. **Open browser** and visit `http://localhost:7860`

### 🎯 Quick Demo

Test all features without starting the web interface:
```bash
python demo.py
```

The demo includes:
- Configuration for all three generation modes
- Service factory functionality showcase
- Configuration option validation
- API endpoint setup verification
- Model compatibility testing

## 📋 User Guide

### 🎯 Generation Mode Selection

The application supports three video generation modes:

#### 1. 📝 Text-to-Video
- **Processing Time**: 1-2 minutes
- **Description**: Generate videos through detailed text descriptions
- **Available Models**: wan2.2-t2v-plus (recommended), wanx2.1-t2v-turbo, wanx2.1-t2v-plus
- **Resolution Support**: 480P-1080P
- **Features**: Style control, aspect ratio, negative prompts, seed control

#### 2. 🖼️ Image-to-Video  
- **Processing Time**: 7-10 minutes
- **Description**: Generate dynamic videos from a single image
- **Available Models**: wan2.2-i2v-flash (fastest), wan2.2-i2v-plus, wanx2.1-i2v-plus, wanx2.1-i2v-turbo
- **Image Requirements**: JPEG/PNG/BMP/WEBP, max 10MB, 360-2000px dimensions
- **Features**: Optional text guidance, style control

#### 3. 🎞️ Keyframe-to-Video
- **Processing Time**: 7-10 minutes  
- **Description**: Generate smooth transitions between start and end frames
- **Available Models**: wanx2.1-kf2v-plus
- **Requirements**: Two images with similar composition (start and end frames)
- **Features**: Optional transition guidance, style control

### Basic Usage

1. **Select Generation Mode**: Choose the desired generation mode at the top of the interface

2. **Input Content** (based on selected mode):
   - **Text Mode**: Enter video description
     - Example: "A peaceful sunset on a mountain ridge with birds flying"
   - **Image Mode**: Upload an image
   - **Keyframe Mode**: Upload start and end images

3. **Choose Style**: Select from available artistic styles
   - Auto (recommended), Cinematic, Anime, Realistic, Abstract, Documentary, Commercial

4. **Set Aspect Ratio**: Choose video dimensions
   - 16:9 (widescreen), 1:1 (square), 9:16 (portrait)

5. **Click "Generate Video"**: Wait for AI to create your video

### Advanced Settings

For text-to-video mode, expand the "Advanced Settings" section for more control:

- **Negative Prompt**: Specify content to avoid in the video
  - Example: "blurry, low quality, distorted"

- **Seed**: Enter a number for reproducible results
  - Same seed + same prompt = similar videos

- **Model Selection**: Choose different models based on needs
  - wan2.2-t2v-plus: Latest high-quality model (recommended)
  - wanx2.1-t2v-turbo: Fast generation model
  - wanx2.1-t2v-plus: High-quality generation model

### Command Line Options

```
python main.py [OPTIONS]

Options:
  --host TEXT       Bind server to specified host (default: 127.0.0.1)
  --port INTEGER    Port to run server on (default: 7860)
  --share           Create public link for the application
  --debug           Enable debug mode with verbose logging
  --check-env       Check environment configuration and exit
  --help            Show this help message and exit
```

#### Usage Examples

```bash
# Run on different port
python main.py --port 8080

# Create public link (for sharing)
python main.py --share

# Debug mode with verbose logging
python main.py --debug

# Check environment configuration
python main.py --check-env

# Bind to all network interfaces
python main.py --host 0.0.0.0
```

## 🏗️ Project Structure

```
Wan_Gateway/
├── src/                           # Core source code directory
│   ├── __init__.py                # Package initialization
│   ├── config.py                  # Configuration management
│   ├── base_video_service.py      # Base video service class
│   ├── text_to_video_service.py   # Text-to-video service
│   ├── image_to_video_service.py  # Image-to-video service
│   ├── keyframe_to_video_service.py # Keyframe-to-video service
│   ├── video_service_factory.py   # Service factory and multi-modal app
│   ├── gradio_app.py              # Gradio web interface
│   ├── oss_service.py             # OSS cloud storage service
│   └── utils.py                   # Utility functions
├── doc/                           # Chinese documentation
│   ├── README_zh.md               # Chinese README
│   ├── API_zh.md                  # Chinese API documentation
│   ├── DEPLOYMENT_zh.md           # Chinese deployment guide
│   ├── CONTRIBUTING_zh.md         # Chinese contributing guide
│   └── CHANGELOG_zh.md            # Chinese changelog
├── .env.example                   # Environment variables template
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project configuration file
├── main.py                        # Application entry point
├── demo.py                        # Feature demonstration script
├── Dockerfile                     # Docker container configuration
├── docker-compose.yml             # Docker Compose configuration
├── deploy-production.sh           # Production deployment script
├── README.md                      # Project documentation (English)
├── API.md                         # API documentation (English)
├── DEPLOYMENT.md                  # Deployment guide (English)
├── CONTRIBUTING.md                # Contributing guide (English)
└── CHANGELOG.md                   # Version changelog (English)
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|----------|
| `DASHSCOPE_API_KEY` | Alibaba Bailian API key | Yes | - |
| `OSS_ACCESS_KEY_ID` | OSS access key ID (optional) | No | - |
| `OSS_ACCESS_KEY_SECRET` | OSS access key secret (optional) | No | - |
| `OSS_ENDPOINT` | OSS service endpoint (optional) | No | https://oss-cn-hangzhou.aliyuncs.com |
| `OSS_BUCKET_NAME` | OSS bucket name (optional) | No | wan-gateway-images |

### Application Settings

Key configuration options in `src/config.py`:

```python
# UI Settings
MAX_PROMPT_LENGTH = 1000        # Maximum prompt length
DEFAULT_STYLE = "<auto>"        # Default style selection
DEFAULT_ASPECT_RATIO = "16:9"   # Default aspect ratio
DEFAULT_MODEL = "wan2.2-t2v-plus" # Default model

# API Settings
MAX_RETRIES = 3                 # Maximum retry attempts
POLLING_INTERVAL = 2            # Text-to-video polling interval (seconds)
KEYFRAME_POLLING_INTERVAL = 30  # Image/keyframe polling interval (seconds)
REQUEST_TIMEOUT = 30            # Request timeout (seconds)
MAX_POLL_TIME = 300             # Text generation max polling time (5 minutes)
KEYFRAME_MAX_POLL_TIME = 900    # Keyframe generation max polling time (15 minutes)

# Image Upload Settings
IMAGE_UPLOAD_CONFIG = {
    "max_size_mb": 10,
    "allowed_formats": ["JPEG", "JPG", "PNG", "BMP", "WEBP"],
    "min_dimension": 360,
    "max_dimension": 2000
}
```

## 🎨 Supported Style Options

| Style | Description | Use Cases |
|-------|-------------|----------|
| **Auto** | Automatic style selection | General use, recommended |
| **Cinematic** | Movie-quality with dramatic lighting | Professional videos, trailers |
| **Anime** | Animation/cartoon style | Character-focused content |
| **Realistic** | Photorealistic rendering | Documentary-style content |
| **Abstract** | Artistic non-realistic style | Creative artistic videos |
| **Documentary** | Natural, informational style | Educational content |
| **Commercial** | Polished advertising style | Marketing materials |

## 📐 Aspect Ratio Options

| Ratio | Description | Use Cases |
|-------|-------------|----------|
| **16:9** | Widescreen format | YouTube, web videos, presentations |
| **1:1** | Square format | Instagram posts, social media |
| **9:16** | Portrait/vertical format | TikTok, Instagram stories, mobile |

## 🐛 Troubleshooting

### Common Issues

#### 1. Configuration Errors
```
❌ Configuration error: DASHSCOPE_API_KEY environment variable is required
```
**Solution**: Ensure your `.env` file contains a valid API key:
```bash
DASHSCOPE_API_KEY=your_actual_api_key_here
```

#### 2. Import Errors
```
❌ Import error: No module named 'gradio'
```
**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

#### 3. Connection/Timeout Errors
```
❌ Connection error - please check your internet connection
```
**Solutions**:
- Check internet connection
- Verify API key is valid and has quota
- Try again later (may be rate limited)

#### 4. Generation Failures
```
❌ Generation failed: Invalid request
```
**Solutions**:
- Ensure prompt is descriptive and appropriate
- Try different styles or aspect ratios
- Check prompt is within length limit (1000 characters)

### Debug Mode

Enable debug mode for detailed logging:
```bash
python main.py --debug
```

This provides detailed output including:
- API request/response details
- Error stack traces
- Performance metrics
- Configuration validation steps

## 📊 Performance Optimization Tips

### Getting Better Generation Results

1. **Descriptive Prompts**: Include details about:
   - Scene setting and environment
   - Lighting conditions (sunset, bright, dim)
   - Camera movement (pan, zoom, static)
   - Mood and atmosphere

2. **Optimal Prompt Length**: 
   - Target 50-200 characters
   - Include key visual elements
   - Avoid overly complex descriptions

3. **Style Selection**:
   - Use "Auto" for general content
   - Choose specific styles for targeted aesthetics
   - "Cinematic" works well for dramatic scenes

4. **Aspect Ratio Selection**:
   - 16:9 for most web/YouTube content
   - 1:1 for social media posts
   - 9:16 for mobile-first content

### Better Performance

1. **System Requirements**:
   - Stable internet connection
   - Modern web browser
   - Sufficient system memory

2. **API Usage**:
   - Respect rate limiting
   - Monitor quota usage
   - Use caching for repeated requests

## 🔌 API Integration Guide

This application integrates with Alibaba Bailian's multi-modal video generation APIs:

### Supported Models

- **Text-to-Video**: wan2.2-t2v-plus, wanx2.1-t2v-turbo, wanx2.1-t2v-plus
- **Image-to-Video**: wan2.2-i2v-flash, wan2.2-i2v-plus, wanx2.1-i2v-plus, wanx2.1-i2v-turbo
- **Keyframe-to-Video**: wanx2.1-kf2v-plus

### Response Handling
- **Asynchronous Processing** with task polling
- **Status Monitoring** (PENDING → RUNNING → SUCCEEDED/FAILED)
- **Automatic Retry** for failed requests
- **Timeout Handling** (5 minutes for text, 15 minutes max for image/keyframe)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Ensure code quality and documentation
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Alibaba Cloud** for providing Bailian multi-modal video generation APIs
- **Gradio** for the excellent web interface framework  
- **Python Community** for outstanding libraries and tools

## 📞 Technical Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Run environment check: `python main.py --check-env`
3. Enable debug mode: `python main.py --debug`
4. Check application logs for detailed error information

For Chinese documentation, see the [doc](doc/) folder.

## 🚦 Project Status

- ✅ Complete multi-modal video generation functionality
- ✅ Robust error handling and logging
- ✅ Comprehensive documentation
- ✅ Production-ready code
- ✅ Docker and cloud deployment support
- ✅ OSS cloud storage integration

---

**Built with ❤️ using Python and Gradio**