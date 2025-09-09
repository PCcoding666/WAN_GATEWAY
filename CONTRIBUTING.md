# 🤝 Contributing Guide

Thank you for your interest in the Wan Gateway project! We welcome all forms of contributions, including code contributions, documentation improvements, issue reporting, and feature suggestions.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Environment Setup](#development-environment-setup)
- [Commit Guidelines](#commit-guidelines)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)

## 📜 Code of Conduct

Participating in this project means you agree to abide by our code of conduct:

- **Respect Others** - Maintain friendliness and professionalism
- **Constructive Communication** - Provide helpful feedback and suggestions
- **Inclusivity** - Welcome contributors of different backgrounds and experience levels
- **Collaborative Spirit** - Work together to improve the project

## 🚀 How to Contribute

### 1. Fork the Project

```bash
git clone https://github.com/your-username/WAN_GATEWAY.git
cd Wan_Gateway
git remote add upstream https://github.com/PCcoding666/WAN_GATEWAY.git
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 3. Make Changes and Commit

```bash
git add .
git commit -m "feat: add batch image processing feature"
git push origin feature/your-feature-name
```

### 4. Create Pull Request

1. Visit your fork on GitHub
2. Click "Compare & pull request"
3. Fill out the PR template
4. Wait for code review

## 💻 Development Environment Setup

### Prerequisites
- Python 3.13+
- Git
- Text editor or IDE (VS Code, PyCharm recommended)

### Installation Steps

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env file and enter your API key

# Verify installation
python main.py --check-env
```

## 📝 Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Commit Format
```
<type>[optional scope]: <description>

[optional body]
[optional footer]
```

### Type Descriptions

| Type | Description | Example |
|------|------|------|
| `feat` | New feature | `feat: add batch video generation` |
| `fix` | Bug fix | `fix: resolve upload size limit issue` |
| `docs` | Documentation changes | `docs: update API documentation` |
| `style` | Code formatting | `style: format code style` |
| `refactor` | Code refactoring | `refactor: restructure service factory` |
| `test` | Add tests | `test: add unit tests` |

## 🎨 Code Standards

### Python Code Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) standards:

```python
class VideoService:
    """Base class for video generation services."""
    
    def __init__(self, api_key: str):
        """Initialize service."""
        self.api_key = api_key
        self._session = requests.Session()
    
    def generate_video(self, prompt: str) -> VideoResult:
        """Generate video."""
        pass
```

### Code Formatting

Use `black` for code formatting:

```bash
# Format all Python files
black .

# Check formatting
black --check .
```

### Type Annotations

Use type annotations to improve code readability:

```python
from typing import Optional, Dict, Any

def process_video_request(
    prompt: str,
    style: Optional[str] = None,
    options: Dict[str, Any] = None
) -> VideoResult:
    """Process video request."""
    pass
```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src

# Run verbose tests
python -m pytest -v
```

### Writing Tests

```python
import pytest
from src.text_to_video_service import TextToVideoService

class TestTextToVideoService:
    def setup_method(self):
        self.service = TextToVideoService("test_api_key")
    
    def test_generate_video_success(self):
        # Test implementation
        pass
    
    def test_generate_video_empty_prompt(self):
        with pytest.raises(ValueError):
            self.service.generate_video("")
```

## 🏆 Recognition

We appreciate every contributor's efforts:

- **Code Contributors** - Listed in the project
- **Documentation Contributors** - Acknowledged in documentation
- **Active Contributors** - Special badges and recognition

## 📞 Getting Help

If you encounter issues while contributing:

1. Check project documentation
2. Search existing Issues
3. Ask questions in Issues
4. Contact project maintainers

For Chinese documentation, see the [doc](doc/) folder.

---

**Happy Coding!** 🚀