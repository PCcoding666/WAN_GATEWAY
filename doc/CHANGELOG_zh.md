# 📝 Wan Gateway 更新日志

本文件记录了 Wan Gateway 多模态视频生成器的所有重要变更。

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 规范，
版本号遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/) 规范。

## [未发布]

### 计划功能
- 支持更多视频格式输出
- 批量处理功能
- 用户账户系统
- 视频历史记录管理

## [2.2.0] - 2026-10-31

### 新增
- GitHub Actions **CI**（`ci.yml`）：pytest、编译检查、UI/CLI/demo dry-run 冒烟、Docker 构建与启动探活。
- GitHub Actions **Deploy to production**（`deploy.yml`）：推送 Artifact Registry → 部署 Cloud Run → 探活；缺少 `GCP_PROJECT_ID` / `GCP_SA_KEY` / `DASHSCOPE_API_KEY` 时跳过并提示；可手动指定 `image_tag` 回滚。
- `.dockerignore`；`docker-compose.yml` 传递地域 / OSS / dry-run 变量并挂载 `./data`。

### 变更
- Dockerfile：Python 3.13，临时安装工具链编译 `oss2` 依赖的 `crcmod`，非 root 用户，`HEALTHCHECK`，支持 `$PORT`。
- `main.py` 读取环境变量 `HOST` / `PORT`。

## [2.1.0] - 2026-10-31

### 新增
- 🖼️ **图像 Tab + `cli.py image`**：万相 2.7 Image (Pro)、万相 2.6 Image / t2i、千问 Qwen-Image 3.0 / 2.1 / 2.0、Qwen-Image-Edit —— 文生图、指令 / 参考编辑、组图（`n`）、预设或自定义 `W*H` 尺寸。
- 🔊 **语音 Tab + `cli.py tts`**：Qwen3-TTS Flash、Qwen-Audio 3.1 TTS、CosyVoice 3.5 / 3 / 2 —— 音色、语种、风格指令、格式、采样率、语速。
- ✂️ **视频编辑任务**：`wan2.7-videoedit` 与 `wan3.0-video`（源视频 URL + 可选参考图）。
- `src/catalog.py`、`src/media_builder.py`、`WanClient.call_sync / submit_async / download_file`、`cli.py catalog`；新增 19 个单测（共 64 个）。

### 变更
- UI 改为 视频 / 图像 / 语音 三个 Tab；图像与语音结果同样写入历史记录。
- 新增 `WAN_DEFAULT_IMAGE_MODEL`、`WAN_DEFAULT_IMAGE_EDIT_MODEL`、`WAN_DEFAULT_SPEECH_MODEL`；产物保存在 `~/.wan_gateway/{videos,images,audio}`。

## [2.0.0] - 2026-10-10

### 新增
- 🆕 **Wan 3.0**（`wan3.0-video`）成为所有任务默认模型：2–30 s、智能时长（-1）、自适应比例、1080P、原生音频。
- ✅ **Wan 2.7**（`wan2.7-t2v / i2v / r2v`）与 **Wan 2.6**（`wan2.6-t2v / i2v / i2v-flash / r2v / r2v-flash`），支持 `input.media`、`shot_type`、2–15 s 时长。
- 🎭 **参考生视频** 任务；🔍 请求预览 + dry-run；🕘 任务历史、按 id 恢复、取消排队任务。
- 📚 声明式模型注册表 `src/models.py`、请求构建器 `src/request_builder.py`、地域感知客户端 `src/wan_client.py`、历史存储 `src/history.py`。
- 🖥️ `cli.py`：`models | generate | status | history`。
- 🌐 `DASHSCOPE_REGION` 等新环境变量，见 `.env.example`。

### 变更
- UI 重写为 `WanStudio`：四个任务共用一个表单，控件随模型自适应；兼容 Gradio 5 / 6。
- 旧服务类改为经由统一构建器生成请求；`negative_prompt` / `audio_url` 按官方结构移入 `input`。
- Wan 2.5 / 2.2 标记为 legacy 默认隐藏，Wan 2.1 标记为 deprecated；`oss2` 变为可选依赖。

## [1.2.0] - 2024-01-08

### 新增
- 🆕 **多模态视频生成支持**
  - 文本生成视频 (Text-to-Video)
  - 图像生成视频 (Image-to-Video) 
  - 关键帧生成视频 (Keyframe-to-Video)
- 🏭 **服务工厂模式** - 统一的服务创建和管理
- 📱 **增强的 Gradio 界面** - 支持模式切换和动态UI
- ☁️ **OSS 云存储集成** - 支持阿里云 OSS 图像存储
- 🔧 **新增模型支持**:
  - wan2.2-t2v-plus (推荐文本生成视频模型)
  - wan2.2-i2v-flash (最快图像生成视频模型)
  - wan2.2-i2v-plus (高质量图像生成视频模型)
  - wanx2.1-kf2v-plus (关键帧生成视频模型)
- 📊 **智能轮询策略** - 不同模式使用不同的轮询间隔
- 🛠️ **完整的部署支持**:
  - Docker 和 Docker Compose 配置
  - 生产环境部署脚本
  - 云端部署指南 (Google Cloud, AWS, 阿里云)
- 📚 **全面的文档更新**:
  - 完整的 API 文档
  - 详细的部署指南
  - 中英文双语支持

### 改进
- ⚡ **性能优化**
  - 异步处理优化
  - 更智能的错误重试机制
  - 资源使用优化
- 🔒 **安全增强**
  - 环境变量安全管理
  - API 密钥验证改进
  - 文件上传安全检查
- 🎨 **用户体验改进**
  - 更直观的界面设计
  - 实时状态反馈
  - 详细的错误提示
- 📦 **代码结构优化**
  - 模块化设计
  - 更好的代码组织
  - 统一的错误处理

### 修复
- 🐛 修复文件路径处理问题
- 🐛 解决内存泄漏问题
- 🐛 修复并发请求处理
- 🐛 解决配置加载异常

### 变更
- 📝 项目名称从 "Enhanced Multi-Modal Video Generator" 更新为 "Wan Gateway"
- 🔄 API 端点结构调整
- 📋 配置文件格式更新
- 🏷️ 版本号从 1.0.0 升级到 1.2.0

### 移除
- 🗑️ 移除过时的 API 兼容性代码
- 🗑️ 清理未使用的依赖项

## [1.1.0] - 2023-12-15

### 新增
- 🎯 **高级设置支持**
  - 负面提示 (Negative Prompts)
  - 种子控制 (Seed Control)
  - 自定义宽高比
- 🎨 **更多风格选项**
  - 电影级 (Cinematic)
  - 动漫 (Anime) 
  - 写实 (Realistic)
  - 抽象 (Abstract)
  - 纪录片 (Documentary)
  - 广告 (Commercial)
- 📊 **状态监控** - 实时生成进度追踪
- 🔄 **自动重试机制** - 网络错误自动重试

### 改进
- ⚡ 生成速度优化 30%
- 🎨 界面美化和用户体验提升
- 📝 错误信息更加友好和详细
- 🔧 配置管理改进

### 修复
- 🐛 修复长提示截断问题
- 🐛 解决网络超时处理
- 🐛 修复特殊字符编码问题

## [1.0.0] - 2023-11-20

### 新增
- 🎬 **基础文本生成视频功能**
  - 支持阿里巴巴百炼 API
  - 基础 Gradio 网页界面
  - 简单的提示输入和视频输出
- ⚙️ **核心配置系统**
  - 环境变量管理
  - API 密钥配置
  - 基础错误处理
- 🐳 **Docker 支持**
  - 基础 Dockerfile
  - Docker Compose 配置
- 📚 **初始文档**
  - README 文档
  - 基础使用说明
  - 安装指南

### 技术栈
- Python 3.8+
- Gradio 4.0+
- 阿里巴巴 DashScope API
- Docker

## [0.1.0] - 2023-10-15

### 新增
- 🏗️ 项目初始化
- 📋 基础项目结构
- 🔧 开发环境配置
- 📄 许可证和基础文档

---

## 版本说明

### 版本号格式
- **主版本号**: 重大功能变更或不兼容的 API 修改
- **次版本号**: 新功能添加，向后兼容
- **修订版本号**: Bug 修复，向后兼容

### 变更类型
- `新增` - 新功能
- `改进` - 现有功能的增强
- `修复` - Bug 修复
- `变更` - 现有功能的修改
- `移除` - 移除的功能
- `安全` - 安全相关的修复

### 图标说明
- 🆕 新功能
- ⚡ 性能改进
- 🐛 Bug 修复
- 🔒 安全更新
- 📚 文档更新
- 🎨 界面改进
- 🔧 配置更改
- 📦 依赖更新
- 🗑️ 移除功能

---

**感谢所有贡献者！** 🎉

如果您发现任何问题或有改进建议，请在 [GitHub Issues](https://github.com/PCcoding666/WAN_GATEWAY/issues) 中提出。