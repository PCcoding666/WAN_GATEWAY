# 📡 Wan Gateway API 文档

本文档详细说明了 Wan Gateway 多模态视频生成器的 API 接口、数据模型和集成指南。

## 📋 目录

- [概述](#概述)
- [认证](#认证)
- [核心服务](#核心服务)
- [数据模型](#数据模型)
- [错误处理](#错误处理)
- [使用示例](#使用示例)
- [最佳实践](#最佳实践)

## 🔍 概述

Wan Gateway 提供了三种主要的视频生成服务：

1. **文本生成视频** (`TextToVideoService`)
2. **图像生成视频** (`ImageToVideoService`) 
3. **关键帧生成视频** (`KeyFrameVideoService`)

所有服务都通过统一的工厂模式 (`VideoServiceFactory`) 和多模态应用 (`MultiModalVideoApp`) 进行管理。

## 🔐 认证

### API 密钥配置

```python
from src.config import Config

# API 密钥通过环境变量配置
DASHSCOPE_API_KEY = "your_api_key_here"

# 可选 OSS 配置
OSS_ACCESS_KEY_ID = "your_oss_key_id"
OSS_ACCESS_KEY_SECRET = "your_oss_secret"
```

### 服务初始化

```python
from src.video_service_factory import MultiModalVideoApp

# 使用默认配置
app = MultiModalVideoApp()

# 或指定 API 密钥
app = MultiModalVideoApp(api_key="your_api_key")
```

## ⚙️ 核心服务

### 1. VideoServiceFactory

服务工厂负责根据模式创建相应的服务实例。

```python
from src.video_service_factory import VideoServiceFactory

# 获取支持的模式
modes = VideoServiceFactory.get_supported_modes()
# 返回: ["text_to_video", "image_to_video", "keyframe_to_video"]

# 创建特定服务
service = VideoServiceFactory.create_service("text_to_video", api_key)

# 获取模式描述
description = VideoServiceFactory.get_mode_description("text_to_video")

# 获取可用模型
models = VideoServiceFactory.get_mode_models("text_to_video")

# 获取默认模型
default_model = VideoServiceFactory.get_default_model("text_to_video")

# 验证模式和模型兼容性
error = VideoServiceFactory.validate_mode_and_model("text_to_video", "wan2.2-t2v-plus")
```

### 2. MultiModalVideoApp

多模态应用程序提供了统一的接口来处理所有类型的视频生成。

```python
from src.video_service_factory import MultiModalVideoApp

app = MultiModalVideoApp()

# 生成视频 - 文本模式
result = app.generate_video(
    mode="text_to_video",
    prompt="一个美丽的日落景象",
    style="Cinematic",
    aspect_ratio="16:9",
    model="wan2.2-t2v-plus",
    negative_prompt="模糊，低质量",
    seed=42
)

# 生成视频 - 图像模式
result = app.generate_video(
    mode="image_to_video",
    image_file="/path/to/image.jpg",
    prompt="添加缓慢的云朵移动",
    style="Realistic"
)

# 生成视频 - 关键帧模式
result = app.generate_video(
    mode="keyframe_to_video",
    start_frame_file="/path/to/start.jpg",
    end_frame_file="/path/to/end.jpg",
    prompt="平滑的变换过程"
)

# 获取服务状态
status = app.get_service_status()
```

### 3. TextToVideoService

文本生成视频服务的详细 API。

```python
from src.text_to_video_service import TextToVideoService

service = TextToVideoService(api_key="your_api_key")

# 生成视频
result = service.generate_video(
    prompt="壮观的山脉日出",
    style="Cinematic",           # 可选风格
    aspect_ratio="16:9",         # 宽高比
    model="wan2.2-t2v-plus",    # 模型选择
    negative_prompt="模糊",       # 负面提示
    seed=12345                   # 随机种子
)

# 处理结果
if result.success:
    print(f"视频URL: {result.video_url}")
    print(f"本地路径: {result.local_video_path}")
    print(f"生成时间: {result.generation_time}秒")
else:
    print(f"生成失败: {result.error_message}")
```

### 4. ImageToVideoService

图像生成视频服务的 API。

```python
from src.image_to_video_service import ImageToVideoService

service = ImageToVideoService(api_key="your_api_key")

# 生成视频
result = service.generate_video(
    image_file="/path/to/input.jpg",  # 输入图像路径
    prompt="让花朵在风中摆动",          # 可选指导提示
    style="Realistic",                # 风格选择
    model="wan2.2-i2v-plus"          # 模型选择
)
```

### 5. KeyFrameVideoService

关键帧生成视频服务的 API。

```python
from src.keyframe_to_video_service import KeyFrameVideoService

service = KeyFrameVideoService(api_key="your_api_key")

# 生成视频
result = service.generate_video(
    start_frame_file="/path/to/start.jpg",  # 起始帧
    end_frame_file="/path/to/end.jpg",      # 结束帧
    prompt="缓慢而自然的过渡",               # 过渡指导
    style="Cinematic",                      # 风格
    model="wanx2.1-kf2v-plus"              # 模型
)
```

## 📊 数据模型

### VideoResult

所有视频生成服务返回的结果对象：

```python
@dataclass
class VideoResult:
    success: bool                    # 生成是否成功
    video_url: Optional[str]         # 生成的视频 URL
    local_video_path: Optional[str]  # 本地视频文件路径
    task_id: Optional[str]          # 任务 ID
    error_message: Optional[str]    # 错误信息
    generation_time: Optional[float] # 生成耗时（秒）
    
    # 可选的元数据
    model_used: Optional[str]       # 使用的模型
    style_used: Optional[str]       # 使用的风格
    aspect_ratio: Optional[str]     # 宽高比
```

### 配置模型

```python
# 风格选项
STYLE_OPTIONS = [
    "<auto>",       # 自动
    "Cinematic",    # 电影级
    "Anime",        # 动漫
    "Realistic",    # 写实
    "Abstract",     # 抽象
    "Documentary",  # 纪录片
    "Commercial"    # 广告
]

# 宽高比选项
ASPECT_RATIO_OPTIONS = ["16:9", "1:1", "9:16"]

# 可用模型
MODEL_OPTIONS = {
    "wan2.2-t2v-plus": {
        "name": "wan2.2-t2v-plus",
        "description": "最新模型，增强细节和运动稳定性",
        "resolutions": ["480P", "1080P"],
        "api_type": "text_to_video"
    },
    "wan2.2-i2v-plus": {
        "name": "wan2.2-i2v-plus", 
        "description": "最新图像生成视频模型",
        "resolutions": ["480P", "1080P"],
        "api_type": "image_to_video"
    }
    # ... 更多模型
}
```

## ❌ 错误处理

### 常见错误类型

```python
# 配置错误
class ConfigurationError(Exception):
    """配置相关错误"""
    pass

# API 错误
class APIError(Exception):
    """API 调用错误"""
    pass

# 超时错误
class TimeoutError(Exception):
    """请求超时错误"""
    pass

# 文件错误
class FileProcessingError(Exception):
    """文件处理错误"""
    pass
```

### 错误处理示例

```python
try:
    result = app.generate_video(
        mode="text_to_video",
        prompt="测试提示"
    )
    if not result.success:
        print(f"生成失败: {result.error_message}")
        
except ConfigurationError as e:
    print(f"配置错误: {e}")
except APIError as e:
    print(f"API错误: {e}")
except TimeoutError as e:
    print(f"超时错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 💡 使用示例

### 基本文本生成视频

```python
from src.video_service_factory import MultiModalVideoApp

def generate_simple_video():
    app = MultiModalVideoApp()
    
    result = app.generate_video(
        mode="text_to_video",
        prompt="一只可爱的小猫在花园中玩耍"
    )
    
    if result.success:
        print(f"✅ 视频生成成功！")
        print(f"📹 视频URL: {result.video_url}")
        if result.local_video_path:
            print(f"📁 本地路径: {result.local_video_path}")
    else:
        print(f"❌ 生成失败: {result.error_message}")

generate_simple_video()
```

### 高级配置生成

```python
def generate_advanced_video():
    app = MultiModalVideoApp()
    
    result = app.generate_video(
        mode="text_to_video",
        prompt="科幻城市的未来景象，霓虹灯闪烁",
        style="Cinematic",
        aspect_ratio="16:9", 
        model="wan2.2-t2v-plus",
        negative_prompt="模糊，噪点，低质量",
        seed=42  # 保证可重现性
    )
    
    return result
```

### 图像生成视频

```python
def image_to_video_example():
    app = MultiModalVideoApp()
    
    result = app.generate_video(
        mode="image_to_video",
        image_file="/path/to/beautiful_landscape.jpg",
        prompt="添加缓慢移动的云彩和微风吹过的草地",
        style="Realistic"
    )
    
    return result
```

### 关键帧生成视频

```python
def keyframe_to_video_example():
    app = MultiModalVideoApp()
    
    result = app.generate_video(
        mode="keyframe_to_video", 
        start_frame_file="/path/to/day_scene.jpg",
        end_frame_file="/path/to/night_scene.jpg",
        prompt="从白天到夜晚的自然过渡"
    )
    
    return result
```

### 批量生成

```python
def batch_generation():
    app = MultiModalVideoApp()
    
    prompts = [
        "春天的樱花飘落",
        "夏日的海滩波浪",
        "秋天的落叶纷飞",
        "冬日的雪花飞舞"
    ]
    
    results = []
    for prompt in prompts:
        result = app.generate_video(
            mode="text_to_video",
            prompt=prompt,
            style="Cinematic"
        )
        results.append(result)
        
        if result.success:
            print(f"✅ '{prompt}' 生成成功")
        else:
            print(f"❌ '{prompt}' 生成失败: {result.error_message}")
    
    return results
```

## 🎯 最佳实践

### 1. 性能优化

```python
# 使用合适的轮询间隔
# 文本生成：2秒间隔
# 图像/关键帧生成：30秒间隔

# 设置合理的超时时间
# 文本生成：5分钟
# 图像/关键帧生成：15分钟

# 复用服务实例
app = MultiModalVideoApp()  # 创建一次，多次使用
```

### 2. 错误重试机制

```python
import time
import random

def generate_with_retry(app, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            result = app.generate_video(**kwargs)
            if result.success:
                return result
            
            # 如果是API错误，等待后重试
            if "rate limit" in result.error_message.lower():
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)
    
    return None
```

### 3. 资源管理

```python
def safe_generation(app, **kwargs):
    try:
        # 检查API配额
        status = app.get_service_status()
        if not status['api_configured']:
            raise ConfigurationError("API未正确配置")
        
        # 生成视频
        result = app.generate_video(**kwargs)
        
        # 清理临时文件
        if result.success and result.local_video_path:
            # 处理完成后可以选择删除本地文件
            # os.remove(result.local_video_path)
            pass
            
        return result
        
    except Exception as e:
        logger.error(f"视频生成失败: {e}")
        raise
```

### 4. 日志记录

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def logged_generation(app, **kwargs):
    logger.info(f"开始视频生成: {kwargs}")
    
    start_time = time.time()
    result = app.generate_video(**kwargs)
    end_time = time.time()
    
    if result.success:
        logger.info(f"视频生成成功，耗时: {end_time - start_time:.2f}秒")
    else:
        logger.error(f"视频生成失败: {result.error_message}")
    
    return result
```

## 📚 更多资源

- [主要文档](README.md) - 项目概述和快速开始
- [部署指南](DEPLOYMENT.md) - 详细的部署说明
- [配置文档](src/config.py) - 完整的配置选项
- [示例代码](demo.py) - 功能演示脚本

---

**需要帮助？** 请查看项目的 Issues 页面或提交新的问题。