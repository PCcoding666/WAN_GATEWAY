---
trigger: always_on
alwaysApply: true
rules:
Tongyi Wanxiang Text-to-Video API Rules 🎬
Here are the key rules and guidelines for using the Tongyi Wanxiang Text-to-Video API. The service creates a 5-second, silent video from a text prompt.

Asynchronous Workflow ⏳
The API is asynchronous, which means it's a two-step process. First, you'll send a request to start the video creation task, and the API will immediately give you a task_id. Then, you'll use that task_id to check the status of the task until it's finished and you can get the video URL.

Processing Time: The recommended wan2.2-t2v-plus model usually takes 1-2 minutes. Older models might take longer.

Authentication 🔑
You'll need to include your API Key in the Authorization header for every request.

Header: Authorization

Value: Bearer YOUR_API_KEY

Step 1: Create the Task
You start the process by sending a POST request to the synthesis endpoint. This doesn't return the video, just the ID for the job you just created.

Endpoint: POST https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis

Key Body Parameters:

model (string, required): The model name. It's best to use wan2.2-t2v-plus.

input.prompt (string, required): Your text description of the video.

parameters.size (string, optional): The resolution, which must be in a "width*height" format (e.g., "1920*1080"). Don't use shorthand like "1080p".

Step 2: Get the Video
Now you'll poll the tasks endpoint with a GET request using the task_id you got from Step 1. You'll need to keep checking it every 15 seconds or so until the task_status changes to SUCCEEDED.

Endpoint: GET https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}

Once the task is successful, the response will finally contain the video_url.

Important Notes ❗
URL Expiration: The video_url is temporary and expires after 24 hours. You must download and store the video yourself if you need permanent access.

SDKs: Official SDKs for Python and Java are available to make this two-step process easier, as they handle the polling for you.

Callbacks: To avoid polling, you can set up HTTP callbacks or use RocketMQ to get a notification when your video is ready. This is a more advanced but efficient method.

Rate Limits: By default, you're limited to creating 2 tasks per second and running 2 tasks at the same time.
---
