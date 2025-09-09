# 🎬 Wan Gateway - Multi-Modal Video Generator

一个基于 Gradio 构建的综合性 Web 应用程序，提供直观的界面来使用阿里巴巴的百炼 API 生成视频。支持三种生成模式：文本生成视频、图像生成视频和关键帧生成视频。

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://python.org)
[![Gradio](https://img.shields.io/badge/gradio-5.43.1%2B-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ 核心功能

- **🎥 文本生成视频**: 将文本描述转换为高质量视频
- **🖼️ 图像生成视频**: 从单张图像生成动态视频
- **🎞️ 关键帧生成视频**: 基于起始和结束帧生成平滑过渡视频
- **🎨 多种风格选择**: 支持电影级、动漫、写实等多种艺术风格
- **📐 灵活的宽高比**: 支持 16:9、1:1、9:16 等不同宽高比
- **⚙️ 高级设置**: 支持负面提示、种子控制等精细调节
- **🤖 智能模型选择**: 根据生成模式自动选择最优模型
- **📱 响应式界面**: 美观且用户友好的界面，实时反馈
- **📊 状态跟踪**: 详细的进度和错误报告
- **☁️ OSS 集成**: 可选的阿里云 OSS 存储支持

## 🚀 快速开始

### 环境要求

- Python 3.13 或更高版本
- 有效的阿里巴巴百炼 API 密钥
- 稳定的互联网连接

### 安装步骤

1. **克隆仓库**:
   ```bash
   git clone https://github.com/PCcoding666/WAN_GATEWAY.git
   cd Wan_Gateway
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**:
   复制 `.env.example` 到 `.env` 并填写配置:
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 API 密钥
   DASHSCOPE_API_KEY=your_api_key_here
   ```

4. **运行应用程序**:
   ```bash
   python main.py
   ```

5. **打开浏览器** 访问 `http://localhost:7860`

### 🎯 快速演示

无需启动 Web 界面即可测试所有功能:
```bash
python demo.py
```

演示内容包括:
- 所有三种生成模式的配置
- 服务工厂功能展示
- 配置选项验证
- API 端点设置检查
- 模型兼容性测试

## 📋 使用指南

### 🎯 生成模式选择

应用支持三种视频生成模式：

#### 1. 📝 文本生成视频
- **处理时间**: 1-2 分钟
- **描述**: 通过详细的文本描述生成视频
- **可用模型**: wan2.2-t2v-plus（推荐）、wanx2.1-t2v-turbo、wanx2.1-t2v-plus
- **分辨率支持**: 480P-1080P
- **功能**: 风格控制、宽高比、负面提示、种子控制

#### 2. 🖼️ 图像生成视频  
- **处理时间**: 7-10 分钟
- **描述**: 从单张图像生成动态视频
- **可用模型**: wan2.2-i2v-flash（最快）、wan2.2-i2v-plus、wanx2.1-i2v-plus、wanx2.1-i2v-turbo
- **图像要求**: JPEG/PNG/BMP/WEBP，最大 10MB，360-2000px 尺寸
- **功能**: 可选文本指导、风格控制

#### 3. 🎞️ 关键帧生成视频
- **处理时间**: 7-10 分钟  
- **描述**: 在起始和结束帧之间生成平滑过渡
- **可用模型**: wanx2.1-kf2v-plus
- **要求**: 两张构图相似的图像（起始帧和结束帧）
- **功能**: 可选过渡指导、风格控制

### 基本使用

1. **选择生成模式**: 在界面上方选择所需的生成模式

2. **输入内容**（根据所选模式）：
   - **文本模式**: 输入视频描述
     - 示例: “在山脊上的宁静日落，有鸟儿在飞翔”
   - **图像模式**: 上传一张图像
   - **关键帧模式**: 上传起始和结束两张图像

3. **选择风格**: 从可用的艺术风格中选择
   - 自动（推荐）、电影级、动漫、写实、抽象、纪录片、广告

4. **设置宽高比**: 选择视频尺寸
   - 16:9（宽屏）、1:1（正方形）、9:16（竖屏）

5. **点击“生成视频”**: 等待 AI 创建你的视频

### 高级设置

对于文本生成视频模式，展开“高级设置”部分获得更多控制：

- **负面提示**: 指定在视频中要避免的内容
  - 示例: “模糊、低质量、扰曲”

- **种子**: 输入数字以获得可重现的结果
  - 相同种子 + 相同提示 = 相似观频

- **模型选择**: 根据需求选择不同模型
  - wan2.2-t2v-plus: 最新高质量模型（推荐）
  - wanx2.1-t2v-turbo: 快速生成模型
  - wanx2.1-t2v-plus: 高质量生成模型

### 命令行选项

```
python main.py [OPTIONS]

选项:
  --host TEXT       绑定服务器到指定主机 (默认: 127.0.0.1)
  --port INTEGER    运行服务器的端口 (默认: 7860)
  --share           为应用程序创建公共链接
  --debug           启用详细日志的调试模式
  --check-env       检查环境配置并退出
  --help            显示此帮助信息并退出
```

#### 使用示例

```
# 在不同端口运行
python main.py --port 8080

# 创建公共链接（用于分享）
python main.py --share

# 详细日志的调试模式
python main.py --debug

# 检查环境是否正确配置
python main.py --check-env

# 绑定到所有网络接口上
python main.py --host 0.0.0.0
```

## 🏗️ 项目结构

```
Wan_Gateway/
├── src/                           # 核心源代码目录
│   ├── __init__.py                # 包初始化
│   ├── config.py                  # 配置管理
│   ├── base_video_service.py      # 基础视频服务类
│   ├── text_to_video_service.py   # 文本生成视频服务
│   ├── image_to_video_service.py  # 图像生成视频服务
│   ├── keyframe_to_video_service.py # 关键帧生成视频服务
│   ├── video_service_factory.py   # 服务工厂和多模态应用
│   ├── gradio_app.py              # Gradio Web 界面
│   ├── oss_service.py             # OSS 云存储服务
│   └── utils.py                   # 工具函数
├── .env.example                   # 环境变量模板
├── requirements.txt               # Python 依赖
├── pyproject.toml                 # 项目配置文件
├── main.py                        # 应用程序入口
├── demo.py                        # 功能演示脚本
├── Dockerfile                     # Docker 容器配置
├── docker-compose.yml             # Docker Compose 配置
├── deploy-production.sh           # 生产部署脚本
├── deploy-to-cloud.sh             # 云部署脚本
└── README.md                      # 项目文档
```

## ⚙️ 配置说明

### 环境变量

| 变量 | 描述 | 必需 | 默认值 |
|----------|-------------|----------|----------|
| `DASHSCOPE_API_KEY` | 阿里巴巴百炼 API 密钥 | 是 | - |
| `OSS_ACCESS_KEY_ID` | OSS 访问密钥 ID（可选） | 否 | - |
| `OSS_ACCESS_KEY_SECRET` | OSS 访问密钥（可选） | 否 | - |
| `OSS_ENDPOINT` | OSS 服务端点（可选） | 否 | https://oss-cn-hangzhou.aliyuncs.com |
| `OSS_BUCKET_NAME` | OSS 存储桶名称（可选） | 否 | wan-gateway-images |

### 应用程序设置

`src/config.py` 中的关键配置选项：

```python
# UI 设置
MAX_PROMPT_LENGTH = 1000        # 最大提示长度
DEFAULT_STYLE = "<auto>"        # 默认风格选择
DEFAULT_ASPECT_RATIO = "16:9"   # 默认宽高比
DEFAULT_MODEL = "wan2.2-t2v-plus" # 默认模型

# API 设置
MAX_RETRIES = 3                 # 最大重试次数
POLLING_INTERVAL = 2            # 文本生成视频轮询间隔（秒）
KEYFRAME_POLLING_INTERVAL = 30  # 图像/关键帧轮询间隔（秒）
REQUEST_TIMEOUT = 30            # 请求超时（秒）
MAX_POLL_TIME = 300             # 文本生成最大轮询时间（5分钟）
KEYFRAME_MAX_POLL_TIME = 900    # 关键帧生成最大轮询时间（15分钟）

# 图像上传设置
IMAGE_UPLOAD_CONFIG = {
    "max_size_mb": 10,
    "allowed_formats": ["JPEG", "JPG", "PNG", "BMP", "WEBP"],
    "min_dimension": 360,
    "max_dimension": 2000
}
```

## 🎨 支持的风格选项

| 风格 | 描述 | 适用场景 |
|-------|-------------|----------|
| **自动** | 自动风格选择 | 通用使用，推荐 |
| **电影级** | 电影质量和戏剧性光照 | 专业视频，预告片 |
| **动漫** | 动画/卡通风格 | 角色为主的内容 |
| **写实** | 逼真渲染 | 纪录片风格内容 |
| **抽象** | 艺术性非写实风格 | 创意艺术视频 |
| **纪录片** | 自然、信息性风格 | 教育内容 |
| **广告** | 精致的广告风格 | 营销材料 |

## 📐 宽高比选项

| 比例 | 描述 | 使用场景 |
|-------|-------------|----------|
| **16:9** | 宽屏格式 | YouTube，网络视频，演示文稿 |
| **1:1** | 正方形格式 | Instagram 帖子，社交媒体 |
| **9:16** | 竖屏/垂直格式 | TikTok，Instagram 故事，移动设备 |

## 🐛 故障排除

### 常见问题

#### 1. 环境配置错误
```
❌ Configuration error: DASHSCOPE_API_KEY environment variable is required
```
**解决方案**: 确保您的 `.env` 文件包含有效的 API 密钥：
```bash
DASHSCOPE_API_KEY=your_actual_api_key_here
```

#### 2. 导入错误
```
❌ Import error: No module named 'gradio'
```
**解决方案**: 安装依赖：
```bash
pip install -r requirements.txt
```

#### 3. 连接/超时错误
```
❌ Connection error - please check your internet connection
```
**解决方案**:
- 检查互联网连接
- 验证 API 密钥是否有效且有配额
- 稍后再试（可能被限流）

#### 4. 生成失败
```
❌ Generation failed: Invalid request
```
**解决方案**:
- 确保提示描述详细且合适
- 尝试不同的风格或宽高比
- 检查提示是否在长度限制内（1000 字符）

### 调试模式

启用调试模式进行详细日志记录：
```bash
python main.py --debug
```

这提供详细输出，包括：
- API 请求/响应详细信息
- 错误堆栈跟踪
- 性能指标
- 配置验证步骤

## 📊 性能优化建议

### 获得更好的生成结果

1. **描述性提示**: 包含以下细节：
   - 场景设置和环境
   - 光照条件（日落、明亮、昏暗）
   - 摄像机移动（平移、缩放、静态）
   - 情绪和氛围

2. **最佳提示长度**: 
   - 目标为 50-200 个字符
   - 包含关键视觉元素
   - 避免过于复杂的描述

3. **风格选择**:
   - 通用内容使用"自动"
   - 针对特定美学选择特定风格
   - "电影级"适合戏剧性场景

4. **宽高比选择**:
   - 16:9 适合大多数网络/YouTube 内容
   - 1:1 适合社交媒体帖子
   - 9:16 适合移动优先内容

### 获得更好的性能

1. **系统要求**:
   - 稳定的互联网连接
   - 现代网络浏览器
   - 充足的系统内存

2. **API 使用**:
   - 遵守限流规则
   - 监控配额使用情况
   - 对重复请求使用缓存

## 🔌 API 集成说明

该应用程序集成阿里巴巴百炼的多模态视频生成 API：

### 支持的模型

- **文本生成视频**: wan2.2-t2v-plus, wanx2.1-t2v-turbo, wanx2.1-t2v-plus
- **图像生成视频**: wan2.2-i2v-flash, wan2.2-i2v-plus, wanx2.1-i2v-plus, wanx2.1-i2v-turbo
- **关键帧生成视频**: wanx2.1-kf2v-plus

### 响应处理
- **异步处理** 带任务轮询
- **状态监控** (PENDING → RUNNING → SUCCEEDED/FAILED)
- **自动重试** 处理失败的请求
- **超时处理** (文本5分钟，图像/关键帧15分钟最大值)

## 🤝 贡献指南

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 进行更改
4. 确保代码质量和文档
5. 提交更改 (`git commit -m 'Add amazing feature'`)
6. 推送到分支 (`git push origin feature/amazing-feature`)
7. 打开 Pull Request

## 📜 许可证

本项目根据 MIT 许可证获得许可 - 有关详细信息，请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- **阿里云** 提供百炼多模态视频生成 API
- **Gradio** 提供出色的 Web 界面框架  
- **Python 社区** 提供优秀的库和工具

## 📞 技术支持

如果您遇到任何问题或有疑问：

1. 查看 [故障排除](#-故障排除) 部分
2. 运行环境检查：`python main.py --check-env`
3. 启用调试模式：`python main.py --debug`
4. 查看应用程序日志获取详细错误信息

## 🚦 项目状态

- ✅ 多模态视频生成功能完整实现
- ✅ 强大的错误处理和日志记录
- ✅ 全面的文档
- ✅ 生产就绪的代码
- ✅ Docker 和云部署支持
- ✅ OSS 云存储集成

---

**使用 ❤️ 通过 Python 和 Gradio 构建**