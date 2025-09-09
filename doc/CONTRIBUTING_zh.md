# 🤝 贡献指南

感谢您对 Wan Gateway 项目的关注！我们欢迎所有形式的贡献，包括但不限于代码贡献、文档改进、问题报告和功能建议。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [提交规范](#提交规范)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [文档贡献](#文档贡献)
- [问题报告](#问题报告)

## 📜 行为准则

参与本项目意味着您同意遵守我们的行为准则：

- **尊重他人** - 对所有参与者保持友善和专业
- **建设性沟通** - 提供有益的反馈和建议
- **包容性** - 欢迎不同背景和经验水平的贡献者
- **协作精神** - 共同努力改进项目

## 🚀 如何贡献

### 1. Fork 项目

```bash
# Fork 项目到你的 GitHub 账户
# 然后克隆到本地
git clone https://github.com/your-username/WAN_GATEWAY.git
cd Wan_Gateway

# 添加上游仓库
git remote add upstream https://github.com/PCcoding666/WAN_GATEWAY.git
```

### 2. 创建分支

```bash
# 从主分支创建新的功能分支
git checkout -b feature/your-feature-name

# 或者修复分支
git checkout -b fix/issue-description
```

### 3. 进行修改

根据你的贡献类型进行相应的修改：

- **新功能**: 添加新的功能模块
- **Bug 修复**: 修复已知问题
- **文档改进**: 更新或完善文档
- **性能优化**: 改进代码性能
- **代码重构**: 改进代码结构

### 4. 提交更改

```bash
# 添加修改的文件
git add .

# 提交更改（遵循提交规范）
git commit -m "feat: 添加图像批量处理功能"

# 推送到你的分支
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

1. 在 GitHub 上访问你的 fork
2. 点击 "Compare & pull request"
3. 填写 PR 模板
4. 等待代码审查

## 💻 开发环境设置

### 前提条件

- Python 3.13+
- Git
- 文本编辑器或 IDE (推荐 VS Code, PyCharm)

### 安装步骤

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. 安装开发依赖
pip install -r requirements.txt

# 4. 安装开发工具（可选）
pip install black flake8 pytest mypy

# 5. 设置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥

# 6. 验证安装
python main.py --check-env
```

### 开发工具配置

推荐的 VS Code 扩展：
- Python
- Python Docstring Generator
- GitLens
- Better Comments

## 📝 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交格式

```
<类型>[可选的作用域]: <描述>

[可选的正文]

[可选的脚注]
```

### 类型说明

| 类型 | 描述 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加批量视频生成功能` |
| `fix` | Bug 修复 | `fix: 修复图像上传大小限制问题` |
| `docs` | 文档更改 | `docs: 更新 API 文档` |
| `style` | 代码格式 | `style: 格式化代码风格` |
| `refactor` | 代码重构 | `refactor: 重构服务工厂类` |
| `perf` | 性能改进 | `perf: 优化视频下载速度` |
| `test` | 添加测试 | `test: 添加单元测试` |
| `chore` | 构建过程或工具变更 | `chore: 更新依赖版本` |

### 示例

```bash
# 功能添加
git commit -m "feat(ui): 添加视频预览功能"

# Bug 修复
git commit -m "fix(api): 修复超时处理逻辑"

# 文档更新
git commit -m "docs: 完善部署指南"

# 重大更改
git commit -m "feat!: 重新设计 API 接口

BREAKING CHANGE: API 路径从 /generate 改为 /api/v1/generate"
```

## 🎨 代码规范

### Python 代码风格

我们遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 标准：

```python
# 好的示例
class VideoService:
    """视频生成服务基类。"""
    
    def __init__(self, api_key: str):
        """初始化服务。
        
        Args:
            api_key: API 密钥
        """
        self.api_key = api_key
        self._session = requests.Session()
    
    def generate_video(self, prompt: str) -> VideoResult:
        """生成视频。
        
        Args:
            prompt: 视频描述提示
            
        Returns:
            VideoResult: 生成结果
        """
        # 实现细节...
        pass
```

### 代码格式化

使用 `black` 进行代码格式化：

```bash
# 格式化所有 Python 文件
black .

# 检查格式
black --check .
```

### 类型注解

使用类型注解提高代码可读性：

```python
from typing import Optional, List, Dict, Any

def process_video_request(
    prompt: str,
    style: Optional[str] = None,
    options: Dict[str, Any] = None
) -> VideoResult:
    """处理视频请求。"""
    pass
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def generate_video(self, prompt: str, **kwargs) -> VideoResult:
    """生成视频。

    根据给定的文本提示生成视频内容。

    Args:
        prompt: 视频描述文本，长度不超过1000字符
        **kwargs: 其他可选参数
            style: 视频风格，如 'Cinematic', 'Anime' 等
            aspect_ratio: 宽高比，如 '16:9', '1:1', '9:16'
            model: 使用的模型名称

    Returns:
        VideoResult: 包含生成结果的数据类
            - success: 是否成功
            - video_url: 视频URL
            - error_message: 错误信息（如果有）

    Raises:
        ValueError: 当prompt为空或超过长度限制时
        APIError: 当API调用失败时

    Examples:
        >>> service = TextToVideoService(api_key="your_key")
        >>> result = service.generate_video("美丽的日落")
        >>> if result.success:
        ...     print(f"视频URL: {result.video_url}")
    """
    pass
```

## 🧪 测试指南

### 运行测试

```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest tests/test_video_service.py

# 运行带覆盖率的测试
python -m pytest --cov=src

# 运行详细测试
python -m pytest -v
```

### 编写测试

```python
import pytest
from unittest.mock import Mock, patch
from src.text_to_video_service import TextToVideoService

class TestTextToVideoService:
    """测试文本生成视频服务。"""
    
    def setup_method(self):
        """每个测试方法前的设置。"""
        self.service = TextToVideoService("test_api_key")
    
    def test_generate_video_success(self):
        """测试成功生成视频。"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                'output': {'task_id': 'test_task_id'}
            }
            
            result = self.service.generate_video("test prompt")
            assert result.success
            assert result.task_id == "test_task_id"
    
    def test_generate_video_empty_prompt(self):
        """测试空提示的错误处理。"""
        with pytest.raises(ValueError, match="提示不能为空"):
            self.service.generate_video("")
    
    @pytest.mark.parametrize("prompt,expected", [
        ("短提示", True),
        ("a" * 1000, True),
        ("a" * 1001, False),
    ])
    def test_prompt_validation(self, prompt, expected):
        """测试提示验证。"""
        try:
            self.service._validate_prompt(prompt)
            assert expected
        except ValueError:
            assert not expected
```

### 测试覆盖率

确保新代码有适当的测试覆盖率：

```bash
# 生成覆盖率报告
python -m pytest --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 📚 文档贡献

### 文档类型

1. **代码文档** - 内联注释和文档字符串
2. **用户文档** - README, 使用指南
3. **开发者文档** - API 文档, 架构说明
4. **部署文档** - 安装和部署指南

### 文档标准

- 使用清晰简洁的语言
- 提供实际的代码示例
- 包含必要的截图或图表
- 保持文档与代码同步

### Markdown 规范

```markdown
# 一级标题

## 二级标题

### 代码示例

\`\`\`python
def example_function():
    """示例函数。"""
    return "Hello, World!"
\`\`\`

### 重要提示

> **注意**: 这是一个重要的注意事项。

### 链接

- [内部链接](#section)
- [外部链接](https://example.com)

### 列表

- 项目 1
- 项目 2
  - 子项目 2.1
  - 子项目 2.2
```

## 🐛 问题报告

### 报告 Bug

使用 GitHub Issues 报告问题时，请包含：

1. **问题描述** - 清晰描述问题
2. **复现步骤** - 详细的复现步骤
3. **期望行为** - 你期望的正确行为
4. **实际行为** - 实际发生的情况
5. **环境信息** - 系统、Python 版本等
6. **错误日志** - 相关的错误信息
7. **截图** - 如果适用

### Issue 模板

```markdown
## 问题描述
简洁清晰地描述这个问题。

## 复现步骤
1. 进入 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

## 期望行为
清晰简洁地描述你期望发生的事情。

## 实际行为
描述实际发生的事情。

## 环境信息
- OS: [如 Ubuntu 20.04]
- Python 版本: [如 3.13.0]
- 项目版本: [如 1.2.0]

## 附加信息
添加任何其他相关的上下文信息。
```

### 功能请求

提交功能请求时，请说明：

1. **功能描述** - 你希望的新功能
2. **使用场景** - 为什么需要这个功能
3. **替代方案** - 你考虑过的其他解决方案
4. **实现建议** - 如果有的话

## 🎯 贡献类型

### 代码贡献

- **新功能开发** - 添加新的功能模块
- **Bug 修复** - 修复现有问题
- **性能优化** - 改进代码性能
- **代码重构** - 改善代码结构

### 非代码贡献

- **文档改进** - 完善项目文档
- **翻译工作** - 多语言支持
- **测试用例** - 添加测试覆盖
- **用户反馈** - 使用体验报告

### 社区贡献

- **问题解答** - 帮助其他用户
- **功能建议** - 提出改进意见
- **推广宣传** - 分享项目
- **代码审查** - 参与 PR 审查

## 📋 代码审查

### 审查清单

- [ ] 代码符合项目规范
- [ ] 有适当的测试覆盖
- [ ] 文档已更新
- [ ] 提交信息规范
- [ ] 没有引入安全问题
- [ ] 性能影响可接受

### 审查准则

1. **代码质量** - 可读性、可维护性
2. **功能正确性** - 是否解决了问题
3. **测试完备性** - 测试覆盖率和质量
4. **文档完整性** - 文档是否同步更新
5. **向后兼容性** - 是否破坏现有功能

## 🏆 贡献者奖励

我们感谢每一位贡献者的努力：

- **代码贡献者** - 在项目中列出
- **文档贡献者** - 在文档中致谢
- **活跃贡献者** - 特殊徽章和认可
- **核心贡献者** - 邀请加入核心团队

## 📞 获取帮助

如果你在贡献过程中遇到问题：

1. **查看文档** - 阅读项目文档
2. **搜索 Issues** - 看看是否有类似问题
3. **提问** - 在 Issues 中提问
4. **联系维护者** - 直接联系项目维护者

## 🙏 致谢

感谢所有为项目做出贡献的开发者、用户和支持者！

你的贡献让 Wan Gateway 变得更加强大和完善。

---

**Happy Coding!** 🚀