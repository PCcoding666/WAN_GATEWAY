# 🎬 Wan Gateway 项目概览

## 📖 项目简介

Wan Gateway 是一个功能强大的多模态视频生成器，基于阿里巴巴百炼 API 和 Gradio 框架构建。该项目提供了直观的 Web 界面，支持三种不同的视频生成模式，为用户提供了从文本描述、图像或关键帧生成高质量视频的能力。

## 🌟 核心特性

### 多模态视频生成
- **文本生成视频**: 将文字描述转换为动态视频
- **图像生成视频**: 从静态图片创建动画效果
- **关键帧生成视频**: 在两个关键帧之间生成平滑过渡

### 智能化功能
- 🤖 自动模型选择和优化
- 🎨 多种艺术风格支持 (电影级、动漫、写实等)
- 📐 灵活的宽高比配置 (16:9, 1:1, 9:16)
- ⚙️ 高级参数控制 (负面提示、种子设置)

### 用户体验
- 📱 响应式 Web 界面
- 🔄 实时状态追踪
- 📊 详细的进度反馈
- 🎯 智能错误处理和重试机制

### 技术特性
- ☁️ 云存储集成 (阿里云 OSS)
- 🐳 Docker 容器化部署
- 🚀 多平台云端部署支持
- 🔒 安全的环境配置管理

## 🏗️ 架构设计

### 核心模块

```
Wan Gateway Architecture
├── Web Interface (Gradio)
│   ├── Multi-Modal UI
│   ├── Dynamic Form Components  
│   └── Real-time Feedback
│
├── Service Factory Pattern
│   ├── VideoServiceFactory
│   ├── MultiModalVideoApp
│   └── Service Routing
│
├── Video Generation Services
│   ├── TextToVideoService
│   ├── ImageToVideoService
│   └── KeyFrameVideoService
│
├── Support Services
│   ├── OSS Storage Service
│   ├── Configuration Management
│   └── Utility Functions
│
└── API Integration
    ├── DashScope API Client
    ├── Async Task Polling
    └── Error Handling
```

### 设计模式

- **工厂模式**: 统一的服务创建和管理
- **策略模式**: 不同视频生成策略的灵活切换  
- **观察者模式**: 状态变化的实时通知
- **适配器模式**: API 接口的统一封装

## 📋 支持的模型

### 文本生成视频模型
- `wan2.2-t2v-plus` - 最新高质量模型 (推荐)
- `wanx2.1-t2v-turbo` - 快速生成模型
- `wanx2.1-t2v-plus` - 高质量生成模型

### 图像生成视频模型  
- `wan2.2-i2v-flash` - 最快生成速度 (推荐)
- `wan2.2-i2v-plus` - 最新高质量模型
- `wanx2.1-i2v-plus` - 复杂运动支持
- `wanx2.1-i2v-turbo` - 快速复杂运动

### 关键帧生成视频模型
- `wanx2.1-kf2v-plus` - 关键帧过渡专用模型

## 🎨 风格和配置选项

### 艺术风格
- **自动** - 智能风格选择 (推荐)
- **电影级** - 专业电影质量和戏剧性光照
- **动漫** - 动画/卡通风格  
- **写实** - 逼真的照片级渲染
- **抽象** - 艺术性非写实风格
- **纪录片** - 自然、信息性风格
- **广告** - 精致的商业广告风格

### 宽高比支持
- **16:9** - 宽屏格式 (YouTube, 网页视频)
- **1:1** - 正方形格式 (Instagram, 社交媒体)
- **9:16** - 竖屏格式 (TikTok, 手机优先)

## 📊 性能指标

### 生成时间
- **文本生成视频**: 1-2 分钟
- **图像生成视频**: 7-10 分钟  
- **关键帧生成视频**: 7-10 分钟

### 技术限制
- **提示长度**: 最大 1000 字符
- **图像大小**: 最大 10MB
- **图像尺寸**: 360-2000px 范围
- **支持格式**: JPEG, PNG, BMP, WEBP

### 系统要求
- **Python**: 3.13+
- **内存**: 最少 2GB (推荐 4GB+)
- **存储**: 5GB+ 可用空间
- **网络**: 稳定互联网连接

## 🚀 部署选项

### 本地开发
```bash
pip install -r requirements.txt
python main.py
```

### Docker 部署
```bash
docker build -t wan-gateway .
docker run -p 7860:7860 wan-gateway
```

### 生产环境
```bash
./deploy-production.sh
```

### 云端部署
- Google Cloud Platform
- Amazon Web Services  
- 阿里云 ECS
- 其他云服务提供商

## 🔧 配置管理

### 环境变量
```bash
# 必需配置
DASHSCOPE_API_KEY=your_api_key_here

# 可选 OSS 配置  
OSS_ACCESS_KEY_ID=your_oss_key
OSS_ACCESS_KEY_SECRET=your_oss_secret
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=wan-gateway-images
```

### 应用配置
- 最大提示长度: 1000 字符
- 轮询间隔: 文本 2秒, 图像 30秒
- 超时设置: 文本 5分钟, 图像 15分钟
- 重试机制: 最大 3 次重试

## 📚 文档结构

### 用户文档
- [README.md](README.md) - 项目介绍和快速开始
- [DEPLOYMENT.md](DEPLOYMENT.md) - 详细部署指南
- [API.md](API.md) - API 接口文档

### 开发者文档  
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南
- [CHANGELOG.md](CHANGELOG.md) - 版本更新日志
- 源码注释和文档字符串

### 配置文件
- [pyproject.toml](pyproject.toml) - 项目配置
- [requirements.txt](requirements.txt) - 依赖管理
- [.env.example](.env.example) - 环境变量模板

## 🛠️ 开发工具链

### 核心技术栈
- **Python 3.13+** - 主要编程语言
- **Gradio 5.43.1+** - Web 界面框架
- **Requests** - HTTP 客户端
- **Pillow** - 图像处理
- **OSS2** - 阿里云对象存储

### 开发工具
- **Black** - 代码格式化
- **Flake8** - 代码风格检查  
- **pytest** - 单元测试框架
- **MyPy** - 类型检查

### CI/CD 支持
- GitHub Actions 工作流
- Docker 多阶段构建
- 自动化测试和部署

## 🎯 使用场景

### 内容创作
- 短视频制作
- 社交媒体内容
- 营销材料创建
- 教育内容制作

### 开发集成
- API 服务集成
- 批量视频生成
- 自动化工作流
- 第三方应用嵌入

### 研究和实验
- AI 视频生成研究
- 创意实验项目
- 原型验证
- 技术演示

## 📈 项目路线图

### 当前版本 (v1.2.0)
- ✅ 多模态视频生成
- ✅ 完整的 Web 界面
- ✅ Docker 部署支持
- ✅ 云存储集成

### 未来计划
- 🔄 批量处理功能
- 👥 用户账户系统  
- 📊 使用分析和统计
- 🌐 多语言界面支持
- 🎨 更多艺术风格
- 📱 移动端应用

## 🤝 社区和支持

### 贡献方式
- 代码贡献和功能开发
- 文档改进和翻译
- 问题报告和功能建议
- 使用反馈和经验分享

### 获取帮助
- GitHub Issues - 问题报告和讨论
- 文档查阅 - 详细使用说明
- 社区交流 - 用户经验分享
- 技术支持 - 专业问题解答

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

**Wan Gateway** - 让视频创作变得简单而强大！ 🎬✨