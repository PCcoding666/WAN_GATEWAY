[查看中文文档](CHANGELOG_zh.md)

# 📝 Wan Gateway Changelog

This file records all notable changes to the Wan Gateway multi-modal video generator.

Following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format,
and adhering to [Semantic Versioning 2.0.0](https://semver.org/).

## [Unreleased]

### Planned Features
- Support for more video format outputs
- Batch processing functionality
- User account system
- Video history management

## [2.0.0] - 2026-10-10

### Added
- 🆕 **Wan 3.0** (`wan3.0-video`) as the default for every task: 2–30 s, smart duration (-1), adaptive ratio, 1080P, native audio.
- ✅ **Wan 2.7** (`wan2.7-t2v`, `wan2.7-i2v`, `wan2.7-r2v`) and **Wan 2.6** (`wan2.6-t2v`, `wan2.6-i2v`, `wan2.6-i2v-flash`, `wan2.6-r2v`, `wan2.6-r2v-flash`) with the `input.media` / `shot_type` / `duration` 2–15 s parameters.
- 🎭 **Reference → Video** task (images via OSS upload, video / audio via URL).
- 📚 Declarative model registry (`src/models.py`), request builder (`src/request_builder.py`), region-aware client (`src/wan_client.py`), JSON task history (`src/history.py`).
- 🔍 Request preview + dry-run mode (`--dry-run`, `WAN_DRY_RUN`).
- 🕘 Task history panel with resume-by-task-id and cancel.
- 🖥️ `cli.py` with `models`, `generate`, `status`, `history` sub-commands.
- 🌐 `DASHSCOPE_REGION` / `DASHSCOPE_BASE_URL`; `WAN_SHOW_LEGACY`, `WAN_SHOW_DEPRECATED`, `WAN_DATA_DIR`, `WAN_DEFAULT_*_MODEL` settings.
- 🧪 New unit tests for the builder, client and history (45 tests total).

### Changed
- UI rewritten as `WanStudio`: one form for four tasks; controls re-fit to the selected model. Works on Gradio 5 and 6.
- Legacy services (`TextToVideoService`, `ImageToVideoService`, `KeyFrameVideoService`) now build payloads through the shared builder; `negative_prompt` / `audio_url` moved to `input` per the official schema.
- Wan 2.5 / 2.2 models marked legacy and hidden by default; Wan 2.1 marked deprecated.
- `oss2` is now optional at import time.

## [1.2.0] - 2024-01-08

### Added
- 🆕 **Multi-modal video generation support**
  - Text-to-Video generation
  - Image-to-Video generation
  - Keyframe-to-Video generation
- 🏭 **Service factory pattern** - Unified service creation and management
- 📱 **Enhanced Gradio interface** - Support for mode switching and dynamic UI
- ☁️ **OSS cloud storage integration** - Support for Alibaba Cloud OSS image storage
- 🔧 **New model support**:
  - wan2.2-t2v-plus (recommended text-to-video model)
  - wan2.2-i2v-flash (fastest image-to-video model)
  - wan2.2-i2v-plus (high-quality image-to-video model)
  - wanx2.1-kf2v-plus (keyframe-to-video model)
- 📊 **Smart polling strategy** - Different polling intervals for different modes
- 🛠️ **Complete deployment support**:
  - Docker and Docker Compose configuration
  - Production environment deployment scripts
  - Cloud deployment guides (Google Cloud, AWS, Alibaba Cloud)
- 📚 **Comprehensive documentation updates**:
  - Complete API documentation
  - Detailed deployment guide
  - Bilingual support (English and Chinese)

### Improved
- ⚡ **Performance optimization**
  - Asynchronous processing optimization
  - Smarter error retry mechanisms
  - Resource usage optimization
- 🔒 **Security enhancements**
  - Environment variable security management
  - Improved API key validation
  - File upload security checks
- 🎨 **User experience improvements**
  - More intuitive interface design
  - Real-time status feedback
  - Detailed error messages
- 📦 **Code structure optimization**
  - Modular design
  - Better code organization
  - Unified error handling

### Fixed
- 🐛 Fixed file path handling issues
- 🐛 Resolved memory leak problems
- 🐛 Fixed concurrent request processing
- 🐛 Resolved configuration loading exceptions

### Changed
- 📝 Project name updated from "Enhanced Multi-Modal Video Generator" to "Wan Gateway"
- 🔄 API endpoint structure adjustments
- 📋 Configuration file format updates
- 🏷️ Version number upgraded from 1.0.0 to 1.2.0

### Removed
- 🗑️ Removed outdated API compatibility code
- 🗑️ Cleaned up unused dependencies

## [1.1.0] - 2023-12-15

### Added
- 🎯 **Advanced settings support**
  - Negative prompts
  - Seed control
  - Custom aspect ratios
- 🎨 **More style options**
  - Cinematic, Anime, Realistic, Abstract, Documentary, Commercial
- 📊 **Status monitoring** - Real-time generation progress tracking
- 🔄 **Automatic retry mechanism** - Auto-retry for network errors

### Improved
- ⚡ Generation speed optimized by 30%
- 🎨 Interface beautification and user experience enhancement
- 📝 More friendly and detailed error messages
- 🔧 Configuration management improvements

### Fixed
- 🐛 Fixed long prompt truncation issue
- 🐛 Resolved network timeout handling
- 🐛 Fixed special character encoding issues

## [1.0.0] - 2023-11-20

### Added
- 🎬 **Basic text-to-video functionality**
  - Support for Alibaba Bailian API
  - Basic Gradio web interface
  - Simple prompt input and video output
- ⚙️ **Core configuration system**
  - Environment variable management
  - API key configuration
  - Basic error handling
- 🐳 **Docker support**
  - Basic Dockerfile
  - Docker Compose configuration
- 📚 **Initial documentation**
  - README documentation, Basic usage instructions, Installation guide

### Tech Stack
- Python 3.8+, Gradio 4.0+, Alibaba DashScope API, Docker

## [0.1.0] - 2023-10-15

### Added
- 🏗️ Project initialization
- 📋 Basic project structure
- 🔧 Development environment configuration
- 📄 License and basic documentation

---

## Version Notes

### Version Number Format
- **Major version**: Major feature changes or incompatible API modifications
- **Minor version**: New feature additions, backward compatible
- **Patch version**: Bug fixes, backward compatible

### Change Types
- `Added` - New features
- `Improved` - Enhancements to existing features
- `Fixed` - Bug fixes
- `Changed` - Modifications to existing features
- `Removed` - Removed features
- `Security` - Security-related fixes

### Icon Legend
- 🆕 New features
- ⚡ Performance improvements
- 🐛 Bug fixes
- 🔒 Security updates
- 📚 Documentation updates
- 🎨 Interface improvements
- 🔧 Configuration changes
- 📦 Dependency updates
- 🗑️ Removed features

---

**Thanks to all contributors!** 🎉

If you find any issues or have improvement suggestions, please submit them in [GitHub Issues](https://github.com/PCcoding666/WAN_GATEWAY/issues).

For Chinese documentation, see the [doc](doc/) folder.