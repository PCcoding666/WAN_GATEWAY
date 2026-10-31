[查看中文文档](doc/README_zh.md)

# 🎬 Wan Gateway Studio — Alibaba Cloud AIGC in one place

A Gradio studio **and** a CLI for Alibaba Cloud Model Studio's generative models:

| Tab | Models | Tasks |
|---|---|---|
| 🎬 **Video** | Wan 3.0 · Wan 2.7 · Wan 2.6 (+ legacy 2.5 / 2.2) | text, image (first frame), keyframes, reference, **edit** → video |
| 🖼️ **Image** | Wan 2.7 Image (Pro) · Wan 2.6 Image / t2i · Qwen-Image 3.0 / 2.1 / 2.0 · Qwen-Image-Edit | text → image, instruction / reference editing, image sets |
| 🔊 **Speech** | Qwen3-TTS Flash · Qwen-Audio 3.1 TTS · CosyVoice 3.5 / 3 / 2 | text → speech, style instructions, cloned voices |

Every tab follows the same rule: the selected model re-fits every control to what it
actually supports, the exact request JSON is one click away, and nothing is sent in
dry-run mode.

[![CI](https://github.com/PCcoding666/WAN_GATEWAY/actions/workflows/ci.yml/badge.svg)](https://github.com/PCcoding666/WAN_GATEWAY/actions/workflows/ci.yml)
[![Deploy](https://github.com/PCcoding666/WAN_GATEWAY/actions/workflows/deploy.yml/badge.svg)](https://github.com/PCcoding666/WAN_GATEWAY/actions/workflows/deploy.yml)
[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://python.org)
[![Gradio](https://img.shields.io/badge/gradio-5.43%2B%20%7C%206.x-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🚀 Deploy

Push to `main` → **CI** (tests, dry-run smoke, Docker build) → **Deploy to production** (Artifact Registry → Cloud Run → smoke test).
Set the `GCP_PROJECT_ID`, `GCP_SA_KEY` and `DASHSCOPE_API_KEY` repository secrets once; until then the deploy job is skipped with a notice. Details: [doc/DEPLOYMENT.md](doc/DEPLOYMENT.md#-automated-deployment-github-actions).

## ✨ What's new in 2.1 — image, speech and video editing

- 🖼️ **Image tab**: `wan2.7-image-pro` (up to 4K, image sets, multi-image reference), `wan2.7-image`, `qwen-image-3.0-pro` (flagship text rendering, identity-preserving edits), `qwen-image-2.1-pro/turbo`, `wan2.6-image`, `wan2.6-t2i`, plus legacy `qwen-image-2.0*`, `qwen-image-edit-plus`, `wan2.5/2.2-t2i-*`. Drop images in to switch from generation to editing.
- 🔊 **Speech tab**: `qwen3-tts-flash` (49 voices, 10 languages), `qwen-audio-3.1-tts-plus/flash`, `cosyvoice-v3.5-plus/flash`, `cosyvoice-v3-plus/flash`, `cosyvoice-v2` — voice, language, style instruction, format, sample rate, speed.
- ✂️ **Edit Video** task: `wan2.7-videoedit` (2–10 s, instruction + reference images) and `wan3.0-video` (edit via reference video).
- 🧱 Same harness as video: `src/catalog.py` (image + speech registry), `src/media_builder.py` (payloads), one `WanClient` with sync / async calls, request preview, dry-run, history, CLI `image` / `tts` / `catalog`.
- Not included (not found on Model Studio as public APIs at the time of writing): music generation, `wan2.2-animate`. Text LLMs are used only behind the ✨ Enhance button.

## ✨ What's new in 2.0 (Oct 2026)

**Models — aligned with Model Studio's current line-up** (full matrix: [doc/MODELS.md](doc/MODELS.md))

| Generation | Models | Highlights |
|---|---|---|
| 🆕 **Wan 3.0** | `wan3.0-video` *(default)* | All-in-one: t2v / i2v / first+last frame / reference. **2–30 s**, smart duration (`-1`), adaptive ratio, 1080P, native audio |
| ✅ **Wan 2.7** | `wan2.7-t2v`, `wan2.7-i2v`, `wan2.7-r2v` | 2–15 s (r2v 2–10 s), 720P/1080P, 30 fps, synchronized audio, new `input.media` schema |
| ✅ **Wan 2.6** | `wan2.6-t2v`, `wan2.6-i2v`, `wan2.6-i2v-flash`, `wan2.6-r2v(-flash)` | 2–15 s, **multi-shot** (`shot_type`), audio, Flash variants for speed |
| 🕰️ Legacy | `wan2.5-*-preview`, `wan2.2-*`, `wanx2.1-*` | Still callable; hidden unless `WAN_SHOW_LEGACY=1` |

**Harness — the UI is now a thin layer over a declarative core**

- 🧭 **Model-driven controls** — resolution, aspect ratio, duration range, audio, multi-shot and prompt limits all come from a single registry (`src/models.py`). You cannot build a request the model will reject.
- 🎭 **Reference → Video** task (Wan 3.0 / 2.7 / 2.6 r2v) with image uploads plus pasted video/audio URLs.
- 🔍 **Request preview** — see the exact JSON before it is sent; **dry-run** mode (`--dry-run` / `WAN_DRY_RUN=1`) never calls the API.
- 🕘 **Task history & resume** — every task id is persisted locally (`~/.wan_gateway`); refresh the page, click a row or paste an id to pick a result back up (URLs stay valid 24 h). Queued tasks can be cancelled.
- 🖥️ **CLI** — `python cli.py models | generate | status | history` share the same builder and client as the UI.
- 🌐 **Regions** — `DASHSCOPE_REGION=cn|intl` switches between Beijing and Singapore endpoints.
- 🧱 **One client** (`src/wan_client.py`) + **one request builder** (`src/request_builder.py`) replace the three copy-pasted service submit paths; the old `TextToVideoService` / `ImageToVideoService` / `KeyFrameVideoService` classes still work and now route through the builder.
- ✅ 45 unit / integration tests (`make test`), Gradio 5 and 6 supported.

## 🧩 Architecture

```
src/models.py            ← video ModelSpec registry: ids, tasks, limits, API dialect, status
src/catalog.py           ← image + speech registries (sizes, n, input images, voices, formats)
src/request_builder.py   ← GenerationRequest → exact video JSON (media / label / size / kf2v / r2v)
src/media_builder.py     ← ImageRequest / SpeechRequest → (path, JSON, is_async)
src/wan_client.py        ← submit / status / cancel / wait / download + call_sync / submit_async
src/history.py           ← JSON task history used by UI + CLI
src/gradio_app.py        ← WanStudio: Video / Image / Speech tabs, preview, poller, history
cli.py                   ← same core from the terminal
```

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
   python main.py            # studio UI
   python main.py --dry-run  # explore the UI without an API key
   python cli.py models      # list models from the terminal
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

### 🎯 Tasks

| Task | Inputs | Default model | Typical wait |
|---|---|---|---|
| 📝 Text → Video | prompt | `wan3.0-video` | 2–6 min |
| 🖼️ Image → Video | prompt + first frame | `wan3.0-video` | 2–6 min |
| 🎞️ Keyframes → Video | prompt + first & last frame | `wan3.0-video` (or `wan2.7-i2v`, `wan2.2-kf2v-flash`) | 2–6 min |
| 🎭 Reference → Video | prompt + reference images / clips / audio | `wan3.0-video` (or `wan2.7-r2v`, `wan2.6-r2v`) | 3–6 min |

Image requirements: JPEG / PNG / BMP / WEBP, ≤ 10 MB, 360–2000 px per side. Images are
uploaded to **your OSS bucket** and passed as signed URLs — without OSS credentials the
app falls back to a demo image and says so in the status panel.

### 🖥️ CLI

```bash
python cli.py catalog --all                                 # image + speech models
python cli.py image --model wan2.7-image-pro -p "a fox in a teacup" --n 2 --size 2K --download
python cli.py image --model qwen-image-3.0-pro -p "make it night" --image https://…/a.png
python cli.py tts --model qwen3-tts-flash --text "你好，世界" --voice Cherry --language Chinese --download
python cli.py tts --model cosyvoice-v3-flash --text "..." --instructions "whisper" --format mp3
python cli.py generate --model wan2.7-videoedit --task vedit -p "anime style" --dry-run   # video edit (see --help)
python cli.py models --all                                  # every model, incl. legacy
python cli.py generate --model wan3.0-video -p "a corgi surfing at sunset" --duration -1 --dry-run
python cli.py generate --model wan2.7-i2v --task kf2v -p "slow push-in" \
    --first-frame https://…/a.png --last-frame https://…/b.png --duration 8 --wait
python cli.py status <task_id> --download
python cli.py history
```

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

## 🛠️ Development and Testing

### Prerequisites
- Python 3.13+
- `make` (optional, for convenience)

### Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # OR
   make install
   ```

### Running Tests
This project uses `pytest` for testing.

1. **Run all tests**:
   ```bash
   pytest tests/
   # OR
   make test
   ```

2. **Run with coverage**:
   ```bash
   pytest --cov=src tests/
   # OR
   make test-cov
   ```

### Project Structure for Testing
- `tests/unit/`: Unit tests for individual components (Config, Services)
- `tests/integration/`: Integration tests simulating full workflows
- `tests/conftest.py`: Shared test fixtures and configuration

---

**Built with ❤️ using Python and Gradio**