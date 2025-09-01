---
trigger: always_on
alwaysApply: true
rules:
-Of course. Here is a detailed set of rules for your AI programming IDE on how to use the Tongyi Wanxiang Start-to-End Frame Video Generation API, written in English.

-----

## **Rules for Interacting with the Tongyi Wanxiang Start-to-End Frame Video API**

### 1\. Overview

The Tongyi Wanxiang Start-to-End Frame Video API generates a 5-second, silent video that transitions between a provided start frame (image) and an end frame (image), guided by a text prompt.

This process is computationally intensive and operates asynchronously. **Expect a processing time of 7-10 minutes per video.**

### 2\. Core Workflow (Asynchronous Process)

All interactions with this service follow a two-step asynchronous process:

1.  **Step 1: Create Task**
      * Make an HTTP `POST` request to the video synthesis endpoint with the start frame, end frame, and prompt.
      * The server will immediately respond with a `task_id` if the request is valid.
2.  **Step 2: Query Result**
      * Make an HTTP `GET` request to the tasks endpoint using the `task_id`.
      * Due to the long processing time, you must poll this endpoint periodically. A recommended polling interval is every **30 seconds**.
      * When the `task_status` is `SUCCEEDED`, the response will contain the `video_url`.

**IMPORTANT:** Both the `task_id` and the final `video_url` are valid for only **24 hours**. Videos must be downloaded and stored within this timeframe.

### 3\. Authentication

All API requests must include an `Authorization` header with your API Key.

  * **Header:** `Authorization`
  * **Value:** `Bearer YOUR_DASHSCOPE_API_KEY`

### 4\. Available Model

This API uses a specific model designed for start-to-end frame video generation.

| Model Name | Price (Yuan/sec) | QPS Limit (Task Submission) | Concurrent Running Tasks |
| :--- | :--- | :--- | :--- |
| `wanx2.1-kf2v-plus` | 0.70 | 2 | 2 |

### 5\. API Endpoints

#### 5.1. Step 1: Create Video Generation Task

This endpoint initiates the video generation process by submitting the start/end frames and prompt.

  * **Method:** `POST`
  * **URL:** `https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis`

**Request Headers**

| Header | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Authorization` | string | **Yes** | Your API key. Example: `Bearer sk-xxxx` |
| `Content-Type` | string | **Yes** | Must be set to `application/json`. |
| `X-DashScope-Async`| string | **Yes** | Must be set to `enable` for asynchronous processing. |

**Request Body**

```json
{
  "model": "wanx2.1-kf2v-plus",
  "input": {
    "first_frame_url": "https://wanx.alicdn.com/material/20250318/first_frame.png",
    "last_frame_url": "https://wanx.alicdn.com/material/20250318/last_frame.png",
    "prompt": "Realism style, a black kitten looks up at the sky curiously, the camera gradually rises from a level shot to a final top-down shot of the kitten's curious eyes."
  },
  "parameters": {
    "resolution": "720P"
  }
}
```

**Request Body Parameters**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `model` | string | **Yes** | The model name. Must be `wanx2.1-kf2v-plus`. |
| `input` | object | **Yes** | Contains the core inputs for the video. |
| `input.prompt` | string | Optional | Text prompt describing the desired video transition and content. Max 800 characters. **This parameter must be omitted if `template` is used.** |
| `input.negative_prompt` | string | Optional | Describe what you *don't* want to see. Max 500 characters. Ex: `low quality, blurry, human`. |
| `input.first_frame_url` | string | **Yes** | The URL or Base64 encoded data for the **start frame**. See "Image Input Specifications" for formats. |
| `input.last_frame_url` | string | Optional | The URL or Base64 encoded data for the **end frame**. **This parameter must be omitted if `template` is used.** |
| `input.template` | string | Optional | Name of a video effect template. Ex: `hufu-1`, `solaron`. **If a template is used, you must omit the `prompt` and `last_frame_url` parameters.** |
| `parameters` | object | Optional | Additional parameters to control the output. |
| `parameters.resolution` | string | Optional | Output video resolution. **Currently fixed at `720P`**. |
| `parameters.duration` | integer | Optional | Video duration in seconds. **Currently fixed at `5` seconds.** |
| `parameters.prompt_extend`| boolean | Optional | If `true` (default), an LLM will rewrite the prompt for better results. `false` uses the prompt as-is. |
| `parameters.seed` | integer | Optional | A random seed (0 to 2,147,483,647) for reproducible results. |
| `parameters.watermark` | boolean | Optional | If `true`, adds an "AI Generated" watermark. Default is `false`. |

**Success Response (200 OK)**

This response confirms the task has been queued.

```json
{
    "output": {
        "task_status": "PENDING",
        "task_id": "0385dc79-5ff8-4d82-bcb6-xxxxxx"
    },
    "request_id": "4909100c-7b5a-9f92-bfe5-xxxxxx"
}
```

#### 5.2. Step 2: Query Task Result

This endpoint retrieves the status and result of a previously created task.

  * **Method:** `GET`
  * **URL:** `https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}`

**URL Path Parameters**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `task_id` | string | **Yes** | The ID of the task received from the creation step. |

**Request Headers**

| Header | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Authorization` | string | **Yes** | Your API key. Example: `Bearer sk-xxxx` |

**Success Response (`task_status: SUCCEEDED`)**

```json
{
    "request_id": "ec016349-6b14-9ad6-8009-xxxxxx",
    "output": {
        "task_id": "3f21a745-9f4b-4588-b643-xxxxxx",
        "task_status": "SUCCEEDED",
        "submit_time": "2025-04-18 10:36:58.394",
        "end_time": "2025-04-18 10:45:23.004",
        "video_url": "https://dashscope-result-wlcb.oss-cn-wulanchabu.aliyuncs.com/xxx.mp4?xxxxx",
        "orig_prompt": "Realism style, a black kitten looks up...",
        "actual_prompt": "Realism style, a black kitten looks up..., yellow eyes bright and spirited..."
    },
    "usage": {
        "video_duration": 5,
        "video_count": 1,
        "video_ratio": "standard"
    }
}
```

  * **`task_status` states:** `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELED`.
  * **`video_url`:** The public URL to the generated MP4 video. **Expires in 24 hours.**

### 6\. SDK Usage (Python Example)

The SDK abstracts the asynchronous polling into a single synchronous call.

**Note:** Be aware this synchronous call will block for **7-10 minutes**.

```python
import os
from http import HTTPStatus
from dashscope import VideoSynthesis

# Ensure the API Key is set in your environment variables
api_key = os.getenv("DASHSCOPE_API_KEY")

def generate_start_to_end_video():
    """
    Calls the Tongyi Wanxiang Start-to-End Frame API.
    This is a long-running synchronous call (7-10 minutes).
    """
    # Image inputs can be public URLs, Base64 strings, or local file paths
    start_frame = "https://wanx.alicdn.com/material/20250318/first_frame.png"
    end_frame = "https://wanx.alicdn.com/material/20250318/last_frame.png"
    
    print("Submitting video generation task. This will take 7-10 minutes...")
    
    response = VideoSynthesis.call(
        api_key=api_key,
        model="wanx2.1-kf2v-plus",
        prompt="Realism style, a black kitten looks up at the sky curiously, the camera gradually rises from a level shot to a final top-down shot of the kitten's curious eyes.",
        first_frame_url=start_frame,
        last_frame_url=end_frame
        # resolution is fixed to 720P, so it can be omitted
    )

    if response.status_code == HTTPStatus.OK:
        print("Video generated successfully!")
        print(f"Task ID: {response.output.task_id}")
        print(f"Video URL (valid for 24h): {response.output.video_url}")
    else:
        print("Video generation failed.")
        print(f"Status Code: {response.status_code}")
        print(f"Error Code: {response.code}")
        print(f"Error Message: {response.message}")

if __name__ == '__main__':
    generate_start_to_end_video()

```

### 7\. Image Input Specifications

The `first_frame_url` and `last_frame_url` fields accept three formats:

1.  **Public URL:** A direct, publicly accessible HTTP or HTTPS link to the image.
      * Example: `"https://example.com/images/my_cat.png"`
2.  **Base64 Encoded String:** The image data encoded in Base64 with a data URI prefix.
      * **Format:** `data:{MIME_type};base64,{base64_data}`
      * **Example:** `"data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."`
3.  **Local File Path (SDKs Only):**
      * **Python SDK:** `file://{path}` (e.g., `file:///home/user/img.png` or `file://./relative.png`)
      * **Java SDK:** `file:///{absolute_path}` (e.g., `file:///D:/images/test.png`)

**Image Constraints:**

  * **Formats:** JPEG, PNG (no transparency), BMP, WEBP.
  * **Dimensions:** Width and height must be between 360px and 2000px.
  * **File Size:** Max 10MB.

### 8\. Common Error Codes

| HTTP Status | Error Code (`code`) | Meaning & Solution |
| :--- | :--- | :--- |
| 400 | `InvalidParameter` | The request has invalid parameters. Check parameter names, values, and constraints. |
| 400 | `IPInfringementSuspect`| The input prompt or image is suspected of IP infringement. Modify the input. |
| 400 | `DataInspectionFailed` | The input prompt or image may contain inappropriate or sensitive content. Modify the input. |
| 500 | `InternalError` | A server-side error occurred. Retry the request. If it persists, contact support. |

### 9\. Operational Whitelisting

If your system has a firewall, you must whitelist the following Alibaba Cloud OSS domains to access the generated videos:

```
# OSS Domain List
dashscope-result-bj.oss-cn-beijing.aliyuncs.com
dashscope-result-hz.oss-cn-hangzhou.aliyuncs.com
dashscope-result-sh.oss-cn-shanghai.aliyuncs.com
dashscope-result-wlcb.oss-cn-wulanchabu.aliyuncs.com
dashscope-result-zjk.oss-cn-zhangjiakou.aliyuncs.com
dashscope-result-sz.oss-cn-shenzhen.aliyuncs.com
dashscope-result-hy.oss-cn-heyuan.aliyuncs.com
dashscope-result-cd.oss-cn-chengdu.aliyuncs.com
dashscope-result-gz.oss-cn-guangzhou.aliyuncs.com
dashscope-result-wlcb-acdr-1.oss-cn-wulanchabu-acdr-1.aliyuncs.com
```
---
