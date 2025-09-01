---
trigger: always_on
alwaysApply: true
rules:
Of course. Here is a detailed set of rules and guidelines for your AI programming IDE on how to use the Tongyi Wanxiang Image-to-Video API, written in English.

-----

## **Rules for Interacting with the Tongyi Wanxiang Image-to-Video API**

### 1\. Overview

The Tongyi Wanxiang Image-to-Video API generates a 5-second, silent video based on a provided initial frame (image) and a text prompt. The API operates asynchronously due to the processing time required for video generation.

### 2\. Core Workflow (Asynchronous Process)

All interactions with the video generation service follow a two-step asynchronous process:

1.  **Step 1: Create Task**
      * Make an HTTP `POST` request to the video synthesis endpoint.
      * This request submits your image, prompt, and parameters.
      * The server will immediately respond with a `task_id` if the request is valid. This does not mean the video is ready.
2.  **Step 2: Query Result**
      * Make an HTTP `GET` request to the tasks endpoint, using the `task_id` from Step 1.
      * You must poll this endpoint periodically to check the task status. A recommended polling interval is every 15 seconds.
      * When the `task_status` is `SUCCEEDED`, the response will contain the `video_url`.

**IMPORTANT:** Both the `task_id` and the final `video_url` are valid for only **24 hours**. Videos must be downloaded and stored within this timeframe.

### 3\. Authentication

All API requests must include an `Authorization` header with your API Key.

  * **Header:** `Authorization`
  * **Value:** `Bearer YOUR_DASHSCOPE_API_KEY`

### 4\. Available Models

Different models offer trade-offs between speed, quality, and resolution. The model is specified in the `model` parameter of the creation request.

| Model Name | Key Features & Description | Supported Resolutions | Default Resolution | Duration (sec) |
| :--- | :--- | :--- | :--- | :--- |
| `wan2.2-i2v-plus` | **(Recommended)** Professional version. Better instruction following, camera control, and consistency. | `480P`, `1080P` | `1080P` | 5 |
| `wan2.2-i2v-flash` | **(Recommended)** Flash version. Extremely fast generation speed with good instruction following. | `480P`, `720P` | `720P` | 5 |
| `wanx2.1-i2v-plus` | Older professional version. Good at complex motion and physics. | `720P` | `720P` | 5 |
| `wanx2.1-i2v-turbo`| Older turbo version. Fast, good at complex motion. | `480P`, `720P` | `720P` | 3, 4, or 5 |

### 5\. API Endpoints

#### 5.1. Step 1: Create Video Generation Task

This endpoint initiates the video generation process.

  * **Method:** `POST`
  * **URL:** `https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis`

**Request Headers**

| Header | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Authorization` | string | **Yes** | Your API key. Example: `Bearer sk-xxxx` |
| `Content-Type` | string | **Yes** | Must be set to `application/json`. |
| `X-DashScope-Async` | string | **Yes** | Must be set to `enable` for asynchronous processing. |

**Request Body**

```json
{
  "model": "wan2.2-i2v-plus",
  "input": {
    "prompt": "A cat running on the grass",
    "img_url": "https://cdn.translate.alibaba.com/r/wanx-demo-1.png"
  },
  "parameters": {
    "resolution": "1080P",
    "prompt_extend": true
  }
}
```

**Request Body Parameters**

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `model` | string | **Yes** | The model to use. See the "Available Models" table above. Ex: `wan2.2-i2v-plus`. |
| `input` | object | **Yes** | Contains the core inputs for the video. |
| `input.prompt` | string | Optional | Text prompt describing the desired video content. Max 800 characters. **This parameter is ignored if `template` is used.** |
| `input.negative_prompt` | string | Optional | Describe what you *don't* want to see. Max 500 characters. Ex: `low resolution, worst quality, blurry`. |
| `input.img_url` | string | **Yes** | The URL or Base64 encoded data for the first frame. See "Image Input Specifications" below for formats. |
| `input.template` | string | Optional | Name of a video effect template to apply. Ex: `flying`, `squish`. If used, `prompt` is ignored. Check API docs for model-specific templates. |
| `parameters` | object | Optional | Additional parameters to control the output. |
| `parameters.resolution` | string | Optional | Output video resolution. Valid values depend on the model. Ex: `1080P`, `720P`, `480P`. Defaults to the model's preferred resolution. |
| `parameters.duration` | integer | Optional | Video duration in seconds. Only applicable to `wanx2.1-i2v-turbo` (values: 3, 4, 5). Other models are fixed at 5 seconds. |
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
    "request_id": "4c87e22d-dfaf-95bb-aadc-xxxxxx",
    "output": {
        "task_id": "436310e6-5404-42ef-b875-xxxxxx",
        "task_status": "SUCCEEDED",
        "submit_time": "2025-07-27 21:05:15.212",
        "scheduled_time": "2025-07-27 21:05:15.232",
        "end_time": "2025-07-27 21:07:58.027",
        "video_url": "https://dashscope-result-wlcb.oss-cn-wulanchabu.aliyuncs.com/1d/xxx.mp4?Expires=xxxxxx",
        "orig_prompt": "a cat running on the grass",
        "actual_prompt": "a white cat is running on the grass, its tail held high, with a light gait."
    },
    "usage": {
        "duration": 5,
        "video_count": 1,
        "SR": 1080
    }
}
```

  * **`task_status` states:** `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELED`.
  * **`video_url`:** The public URL to the generated MP4 video. **Expires in 24 hours.**

### 6\. Image Input Specifications

The `img_url` field accepts three formats:

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

### 7\. Billing and Rate Limiting

  * **Billing:** You are charged per second of successfully generated video. Failed tasks incur no cost.
  * **Rate Limits:** Limits are shared across a main account and its RAM sub-accounts.

| Model Series | QPS Limit (Task Submission) | Concurrent Running Tasks |
| :--- | :--- | :--- |
| `wan2.2` models | 2 | 2 |
| `wanx2.1` models | 2 | 2 |

### 8\. Common Error Codes

| HTTP Status | Error Code (`code`) | Meaning & Solution |
| :--- | :--- | :--- |
| 400 | `InvalidParameter` | The request has invalid parameters. Check parameter names, values, and constraints. |
| 400 | `IPInfringementSuspect`| The input prompt or image is suspected of IP infringement. Modify the input. |
| 400 | `DataInspectionFailed` | The input prompt or image may contain inappropriate or sensitive content. Modify the input. |
| 500 | `InternalError` | A server-side error occurred. Retry the request. If it persists, contact support. |

### 9\. Operational Whitelisting

The generated `video_url` points to Alibaba Cloud OSS. If your system has a firewall or strict outbound access policies, you must whitelist the following domains to access the videos:

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
