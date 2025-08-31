# 🎬 Gradio Bailian Text-to-Video Generator

A comprehensive web application built with Gradio that provides an intuitive interface for generating videos from text descriptions using Alibaba's Bailian "wan-v1-t2v" API.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Gradio](https://img.shields.io/badge/gradio-4.0%2B-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

- **🎥 Text-to-Video Generation**: Convert text descriptions into high-quality videos
- **🎨 Multiple Styles**: Choose from various artistic styles (Cinematic, Anime, Realistic, etc.)
- **📐 Flexible Ratios**: Support for different aspect ratios (16:9, 1:1, 9:16)
- **⚙️ Advanced Settings**: Fine-tune generation with negative prompts and seeds
- **📱 Responsive UI**: Beautiful, user-friendly interface with real-time feedback
- **🔄 Loading States**: Clear visual feedback during video generation
- **📊 Status Tracking**: Detailed progress and error reporting
- **🔧 Easy Configuration**: Simple environment setup and deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- A valid Alibaba DashScope API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd gradio-bailian-t2v
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```bash
   DASHSCOPE_API_KEY=your_api_key_here
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

5. **Open your browser** and navigate to `http://localhost:7860`

## 📋 Usage Guide

### Basic Usage

1. **Enter a prompt**: Describe the video you want to generate
   - Example: "A serene sunset over mountains with birds flying"

2. **Select style**: Choose from available artistic styles
   - Auto (Recommended), Cinematic, Anime, Realistic, Abstract, Documentary, Commercial

3. **Choose aspect ratio**: Select video dimensions
   - 16:9 (Widescreen), 1:1 (Square), 9:16 (Portrait)

4. **Click "Generate Video"**: Wait for the AI to create your video

### Advanced Settings

Expand the "Advanced Settings" section for more control:

- **Negative Prompt**: Specify what to avoid in the video
  - Example: "blurry, low quality, distorted"

- **Seed**: Enter a number for reproducible results
  - Same seed + same prompt = similar video

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --host TEXT       Host to bind the server to (default: 0.0.0.0)
  --port INTEGER    Port to run the server on (default: 7860)
  --share           Create a public link for the app
  --debug           Enable debug mode with verbose logging
  --check-env       Check environment configuration and exit
  --help            Show this message and exit
```

#### Examples

```bash
# Run on a different port
python main.py --port 8080

# Create a public link (for sharing)
python main.py --share

# Debug mode with verbose logging
python main.py --debug

# Check if environment is properly configured
python main.py --check-env
```

## 🏗️ Project Structure

```
gradio-bailian-t2v/
├── src/
│   ├── __init__.py                # Package initialization
│   ├── config.py                  # Configuration management
│   ├── text_to_video_service.py   # Core API service
│   ├── gradio_app.py              # Gradio UI implementation
│   └── utils.py                   # Helper functions

├── .env                           # Environment variables (create this)
├── requirements.txt               # Python dependencies
├── main.py                        # Application entry point
└── README.md                      # This documentation
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DASHSCOPE_API_KEY` | Your Alibaba DashScope API key | Yes | - |
| `API_ENDPOINT` | API endpoint URL | No | Official endpoint |

### Application Settings

Key configuration options in `src/config.py`:

```python
# UI Settings
MAX_PROMPT_LENGTH = 1000        # Maximum prompt length
DEFAULT_STYLE = "<auto>"        # Default style selection
DEFAULT_ASPECT_RATIO = "16:9"   # Default aspect ratio

# API Settings
MAX_RETRIES = 3                 # Maximum retry attempts
POLLING_INTERVAL = 2            # Polling interval (seconds)
REQUEST_TIMEOUT = 30            # Request timeout (seconds)
MAX_POLL_TIME = 300            # Maximum polling time (5 minutes)
```

## 🎨 Supported Styles

| Style | Description | Best For |
|-------|-------------|----------|
| **Auto** | Automatic style selection | General use, recommended |
| **Cinematic** | Movie-like quality with dramatic lighting | Professional videos, trailers |
| **Anime** | Animation/cartoon style | Character-focused content |
| **Realistic** | Photorealistic rendering | Documentary-style content |
| **Abstract** | Artistic, non-realistic style | Creative, artistic videos |
| **Documentary** | Natural, informative style | Educational content |
| **Commercial** | Polished, advertisement-style | Marketing materials |

## 📐 Aspect Ratios

| Ratio | Description | Use Case |
|-------|-------------|----------|
| **16:9** | Widescreen format | YouTube, web videos, presentations |
| **1:1** | Square format | Instagram posts, social media |
| **9:16** | Portrait/vertical | TikTok, Instagram stories, mobile |



## 🐛 Troubleshooting

### Common Issues

#### 1. Environment Configuration Error
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
- Check internet connectivity
- Verify API key is valid and has quota
- Try again after a few moments (may be rate limited)

#### 4. Generation Failures
```
❌ Generation failed: Invalid request
```
**Solutions**:
- Ensure prompt is descriptive and appropriate
- Try different styles or aspect ratios
- Check if prompt is within length limits (1000 characters)

### Debug Mode

Enable debug mode for detailed logging:
```bash
python main.py --debug
```

This provides verbose output including:
- API request/response details
- Error stack traces
- Performance metrics
- Configuration validation steps

## 📊 Performance Tips

### For Better Generation Results

1. **Descriptive Prompts**: Include details about:
   - Scene setting and environment
   - Lighting conditions (sunset, bright, dim)
   - Camera movement (pan, zoom, static)
   - Mood and atmosphere

2. **Optimal Prompt Length**: 
   - Aim for 50-200 characters
   - Include key visual elements
   - Avoid overly complex descriptions

3. **Style Selection**:
   - Use "Auto" for general content
   - Choose specific styles for targeted aesthetics
   - "Cinematic" works well for dramatic scenes

4. **Aspect Ratio Choice**:
   - 16:9 for most web/YouTube content
   - 1:1 for social media posts
   - 9:16 for mobile-first content

### For Better Performance

1. **System Requirements**:
   - Stable internet connection
   - Modern web browser
   - Sufficient system memory

2. **API Usage**:
   - Respect rate limits
   - Monitor quota usage
   - Use caching for repeated requests

## 🔌 API Integration

The application integrates with Alibaba Bailian's text-to-video API:

### Request Format
```json
{
  "model": "wanx-v1",
  "input": {
    "text": "Your video description",
    "style": "Cinematic",
    "aspect_ratio": "16:9"
  },
  "parameters": {
    "negative_prompt": "Optional exclusions",
    "seed": 42
  }
}
```

### Response Handling
- **Asynchronous processing** with task polling
- **Status monitoring** (PENDING → RUNNING → SUCCEEDED/FAILED)
- **Automatic retries** for failed requests
- **Timeout handling** (5-minute maximum)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Ensure code quality and documentation
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Alibaba Cloud** for the Bailian text-to-video API
- **Gradio** for the amazing web interface framework
- **Python Community** for excellent libraries and tools

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Run environment check: `python main.py --check-env`
3. Enable debug mode: `python main.py --debug`
4. Check application logs for detailed error information

## 🚦 Status

- ✅ Core functionality implemented
- ✅ Robust error handling and logging
- ✅ Comprehensive documentation
- ✅ Error handling and validation
- ✅ Production-ready code

---

**Built with ❤️ using Python and Gradio**