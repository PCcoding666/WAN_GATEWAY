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