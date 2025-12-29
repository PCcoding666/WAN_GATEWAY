"""
Enhanced Gradio Web Interface for Multi-Modal Video Generation.

This module provides a user-friendly web interface for generating videos
from text, images, or keyframes using the Bailian APIs.
"""
import gradio as gr
import os
import logging
from typing import Tuple, Optional, Dict, Any
from .config import Config
from .video_service_factory import VideoServiceFactory, MultiModalVideoApp
from .text_to_video_service import VideoResult
from .prompt_optimizer import optimize_prompt_with_qwen

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedGradioVideoApp:
    """Enhanced Gradio application for multi-modal video generation."""
    
    def __init__(self):
        """Initialize the Enhanced Gradio application."""
        self.app = MultiModalVideoApp()
        # Store task metadata for async processing
        self.active_tasks = {}  # task_id -> {mode, start_time, params}
        logger.info("Enhanced Gradio Video application initialized")
    
    def generate_video_handler(
        self,
        mode: str,
        # Text-to-Video inputs
        text_prompt: str,
        text_model: str,
        text_style: str,
        text_aspect_ratio: str,
        text_negative_prompt: str,
        text_seed: str,
        text_duration: int,
        text_audio_enabled: bool,
        text_audio_url: str,
        # Image-to-Video inputs
        image_file,
        image_prompt: str,
        image_style: str,
        image_duration: int,
        image_audio_enabled: bool,
        image_audio_url: str,
        # Keyframe-to-Video inputs
        start_frame_file,
        end_frame_file,
        keyframe_prompt: str,
        keyframe_style: str
    ) -> Tuple[Optional[str], str]:
        """
        Handle video generation request from Gradio interface.
        
        Returns:
            Tuple[Optional[str], str]: (video_path, status_message)
        """
        try:
            logger.info(f"Generating video with mode: {mode}")
            
            # Prepare parameters based on mode
            if mode == "Text-to-Video":
                if not text_prompt or not text_prompt.strip():
                    return None, "❌ Please enter a text description for video generation."
                
                # Convert seed to int if provided
                seed_int = None
                if text_seed and text_seed.strip():
                    try:
                        seed_int = int(float(text_seed))
                    except (ValueError, TypeError):
                        return None, "❌ Invalid seed value. Please enter a valid number."
                
                # Process negative prompt
                neg_prompt = text_negative_prompt.strip() if text_negative_prompt else None
                
                # Process audio URL
                audio_url = text_audio_url.strip() if text_audio_url and text_audio_url.strip() else None
                
                result: VideoResult = self.app.generate_video(
                    mode="text_to_video",
                    prompt=text_prompt,
                    model=text_model,
                    style=Config.get_style_value_from_display(text_style),
                    aspect_ratio=text_aspect_ratio,
                    negative_prompt=neg_prompt,
                    seed=seed_int,
                    duration=text_duration,
                    audio_enabled=text_audio_enabled,
                    audio_url=audio_url
                )
                
            elif mode == "Image-to-Video":
                if image_file is None:
                    return None, "❌ Please upload an image for video generation."
                
                # Process audio URL
                audio_url = image_audio_url.strip() if image_audio_url and image_audio_url.strip() else None
                
                result: VideoResult = self.app.generate_video(
                    mode="image_to_video",
                    image_file=image_file,
                    prompt=image_prompt or "",
                    style=Config.get_style_value_from_display(image_style),
                    duration=image_duration,
                    audio_enabled=image_audio_enabled,
                    audio_url=audio_url
                )
                
            elif mode == "Keyframe-to-Video":
                if start_frame_file is None or end_frame_file is None:
                    return None, "❌ Please upload both start and end frame images."
                
                result: VideoResult = self.app.generate_video(
                    mode="keyframe_to_video",
                    start_frame_file=start_frame_file,
                    end_frame_file=end_frame_file,
                    prompt=keyframe_prompt or "",
                    style=Config.get_style_value_from_display(keyframe_style)
                )
            else:
                return None, f"❌ Unsupported generation mode: {mode}"
            
            if result.success:
                # Format status message
                status_msg = f"✅ Video generated successfully"
                if result.generation_time:
                    status_msg += f" in {result.generation_time:.1f}s"
                if result.task_id:
                    status_msg += f" (Task ID: {result.task_id})"
                
                # Prefer local video path for better stability
                video_path = None
                if result.local_video_path and os.path.exists(result.local_video_path):
                    video_path = result.local_video_path
                    status_msg += " - Video downloaded locally"
                elif result.video_url:
                    video_path = result.video_url
                    status_msg += " - Using direct URL"
                    logger.warning("Local download failed, using direct URL")
                else:
                    return None, "❌ Video generated but no valid path available"
                
                return video_path, status_msg
            else:
                error_msg = f"❌ Generation failed: {result.error_message}"
                logger.error(error_msg)
                return None, error_msg
                
        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def submit_task_handler(
        self,
        mode: str,
        # Text-to-Video inputs
        text_prompt: str,
        text_model: str,
        text_style: str,
        text_aspect_ratio: str,
        text_negative_prompt: str,
        text_seed: str,
        text_duration: int,
        text_audio_enabled: bool,
        text_audio_url: str,
        # Image-to-Video inputs
        image_file,
        image_prompt: str,
        image_style: str,
        image_duration: int,
        image_audio_enabled: bool,
        image_audio_url: str,
        # Keyframe-to-Video inputs
        start_frame_file,
        end_frame_file,
        keyframe_prompt: str,
        keyframe_style: str
    ) -> Tuple[str, str, bool]:
        """
        Submit video generation task asynchronously and return task ID.
        
        Returns:
            Tuple[str, str, bool]: (task_id, status_message, timer_active)
        """
        import time as time_module
        
        try:
            logger.info(f"Submitting async task with mode: {mode}")
            
            # Prepare service based on mode
            if mode == "Text-to-Video":
                if not text_prompt or not text_prompt.strip():
                    return "", "❌ Please enter a text description for video generation.", False
                
                self.app.set_mode("text_to_video")
                service = self.app.current_service
                
                # Convert seed to int if provided
                seed_int = None
                if text_seed and text_seed.strip():
                    try:
                        seed_int = int(float(text_seed))
                    except (ValueError, TypeError):
                        return "", "❌ Invalid seed value. Please enter a valid number.", False
                
                # Process prompts
                neg_prompt = text_negative_prompt.strip() if text_negative_prompt else None
                audio_url = text_audio_url.strip() if text_audio_url and text_audio_url.strip() else None
                
                # Build request and submit task
                from .text_to_video_service import TextToVideoService
                if not isinstance(service, TextToVideoService):
                    return "", "❌ Service initialization failed", False
                
                # Build request data
                request_data = service._build_request(
                    prompt=text_prompt,
                    style=Config.get_style_value_from_display(text_style),
                    aspect_ratio=text_aspect_ratio,
                    model=Config.get_model_id_from_display_name(text_model),
                    negative_prompt=neg_prompt,
                    seed=seed_int,
                    duration=text_duration,
                    audio_enabled=text_audio_enabled,
                    audio_url=audio_url
                )
                
                # Submit task
                task_response = service._submit_task(request_data)
                
            elif mode == "Image-to-Video":
                if image_file is None:
                    return "", "❌ Please upload an image for video generation.", False
                
                self.app.set_mode("image_to_video")
                service = self.app.current_service
                
                from .image_to_video_service import ImageToVideoService
                if not isinstance(service, ImageToVideoService):
                    return "", "❌ Service initialization failed", False
                
                # Validate and process image
                validation_error = service._validate_image_inputs(
                    image_file, image_prompt or "", 
                    Config.DEFAULT_IMAGE_TO_VIDEO_MODEL, image_duration
                )
                if validation_error:
                    return "", f"❌ {validation_error}", False
                
                # Process image and upload to OSS
                public_image_url, image_info = service._process_image_upload(image_file)
                if not public_image_url:
                    return "", "❌ Failed to process and upload image", False
                
                # Process audio URL
                audio_url = image_audio_url.strip() if image_audio_url and image_audio_url.strip() else None
                
                # Build request
                request_data = service._build_image_request(
                    public_image_url=public_image_url,
                    prompt=image_prompt.strip() if image_prompt else None,
                    model=Config.DEFAULT_IMAGE_TO_VIDEO_MODEL,
                    duration=image_duration,
                    audio_enabled=image_audio_enabled,
                    audio_url=audio_url
                )
                
                # Submit task
                task_response = service._submit_task(request_data)
                
            elif mode == "Keyframe-to-Video":
                if start_frame_file is None or end_frame_file is None:
                    return "", "❌ Please upload both start and end frame images.", False
                
                self.app.set_mode("keyframe_to_video")
                service = self.app.current_service
                
                from .keyframe_to_video_service import KeyFrameVideoService
                if not isinstance(service, KeyFrameVideoService):
                    return "", "❌ Service initialization failed", False
                
                # Process and upload images
                start_url, start_info = service._process_image_upload(start_frame_file)
                end_url, end_info = service._process_image_upload(end_frame_file)
                
                if not start_url or not end_url:
                    return "", "❌ Failed to process and upload keyframe images", False
                
                # Build request
                request_data = service._build_keyframe_request(
                    start_frame_url=start_url,
                    end_frame_url=end_url,
                    prompt=keyframe_prompt.strip() if keyframe_prompt else None,
                    model=Config.DEFAULT_KEYFRAME_TO_VIDEO_MODEL
                )
                
                # Submit task
                task_response = service._submit_task(request_data)
            else:
                return "", f"❌ Unsupported generation mode: {mode}", False
            
            # Check task submission response
            if not task_response.get('success', False):
                return "", f"❌ {task_response.get('error', 'Failed to submit generation task')}", False
            
            task_id = task_response.get('task_id')
            if not task_id:
                return "", "❌ No task ID received from API", False
            
            # Store task metadata
            self.active_tasks[task_id] = {
                'mode': mode,
                'start_time': time_module.time(),
                'service': service
            }
            
            status_msg = f"✅ Task submitted successfully! Task ID: {task_id}\n⏳ Generating video... This may take several minutes."
            logger.info(f"Task {task_id} submitted for mode {mode}")
            
            # Return task_id, status, and timer_active=True to start polling
            return task_id, status_msg, True
            
        except Exception as e:
            error_msg = f"❌ Unexpected error during task submission: {str(e)}"
            logger.error(error_msg)
            return "", error_msg, False
    
    def check_task_status_handler(self, task_id: str) -> Tuple[Optional[str], str, bool]:
        """
        Check the status of a submitted task (non-blocking).
        
        Args:
            task_id: The task ID to check
            
        Returns:
            Tuple[Optional[str], str, bool]: (video_path, status_message, timer_active)
        """
        import time as time_module
        
        if not task_id:
            return None, "No active task", False
        
        try:
            # Get task metadata
            task_meta = self.active_tasks.get(task_id)
            if not task_meta:
                return None, f"⚠️ Task {task_id} not found in active tasks", False
            
            service = task_meta['service']
            elapsed_time = time_module.time() - task_meta['start_time']
            
            # Check task status
            status_result = service._check_task_status(task_id)
            
            if status_result['status'] == 'SUCCEEDED':
                video_url = status_result.get('video_url')
                if video_url:
                    logger.info(f"Task {task_id} completed in {elapsed_time:.1f}s")
                    
                    # Download video locally
                    local_path = service._download_video_locally(video_url, task_id)
                    
                    # Clean up task from active tasks
                    del self.active_tasks[task_id]
                    
                    video_path = local_path if local_path and os.path.exists(local_path) else video_url
                    status_msg = f"✅ Video generated successfully in {elapsed_time:.1f}s (Task ID: {task_id})"
                    
                    # Return video, status, and timer_active=False to stop polling
                    return video_path, status_msg, False
                else:
                    del self.active_tasks[task_id]
                    return None, "❌ Video generation succeeded but no URL available", False
                    
            elif status_result['status'] == 'FAILED':
                error_msg = status_result.get('error_message', 'Unknown error')
                logger.error(f"Task {task_id} failed: {error_msg}")
                del self.active_tasks[task_id]
                return None, f"❌ Video generation failed: {error_msg}", False
                
            elif status_result['status'] in ['PENDING', 'RUNNING']:
                status_msg = f"⏳ Generating video... ({elapsed_time:.0f}s elapsed)\nStatus: {status_result['status']}\nTask ID: {task_id}"
                # Keep polling
                return None, status_msg, True
                
            else:
                # ERROR or UNKNOWN status
                error_msg = status_result.get('error_message', 'Unknown error')
                status_msg = f"⚠️ Task status check error: {error_msg} ({elapsed_time:.0f}s elapsed)"
                # Keep polling for a bit in case it's a transient error
                return None, status_msg, True
                
        except Exception as e:
            error_msg = f"❌ Error checking task status: {str(e)}"
            logger.error(error_msg)
            # Don't stop polling on exceptions, might be transient
            return None, error_msg, True
    
    def create_interface(self) -> gr.Blocks:
        """
        Create the enhanced Gradio interface with mode selection.
        
        Returns:
            gr.Blocks: Enhanced Gradio interface
        """
        # Prepare model choices for text-to-video
        text_model_choices = []
        for model_id in Config.get_text_to_video_models():
            if model_id in Config.MODEL_OPTIONS:
                model_info = Config.MODEL_OPTIONS[model_id]
                text_model_choices.append(model_info["name"])
        
        # Style options for display
        style_choices = [Config.get_style_display_name(style) for style in Config.STYLE_OPTIONS]
        
        with gr.Blocks(title="🎬 Multi-Modal Video Generator", theme=gr.themes.Soft(), analytics_enabled=False) as interface:
            gr.Markdown("# 🎬 Multi-Modal Video Generator")
            gr.Markdown("Generate videos from text descriptions, single images, or start/end frame pairs using Alibaba's Bailian APIs.")
            
            with gr.Row():
                mode_selector = gr.Radio(
                    choices=["Text-to-Video", "Image-to-Video", "Keyframe-to-Video"],
                    label="🎯 Generation Mode",
                    value="Text-to-Video",
                    info="Choose how you want to generate your video"
                )
            
            # Text-to-Video inputs
            with gr.Group(visible=True) as text_group:
                gr.Markdown("### 📝 Text-to-Video Generation")
                
                # Main Prompt Area
                with gr.Row():
                    text_prompt = gr.Textbox(
                        label="Video Description",
                        placeholder="Describe the video you want to generate...",
                        lines=3,
                        scale=4
                    )
                    optimize_btn = gr.Button("✨ Optimize\nPrompt", size="sm", variant="secondary", scale=1)

                # Primary Options
                with gr.Row():
                    text_model = gr.Dropdown(
                        label="Model",
                        choices=text_model_choices,
                        value=text_model_choices[0] if text_model_choices else "Wanxiang 2.2 Pro"
                    )
                    text_style = gr.Dropdown(
                        label="Style",
                        choices=style_choices,
                        value=style_choices[0] if style_choices else "Auto"
                    )
                    text_aspect_ratio = gr.Dropdown(
                        label="Aspect Ratio",
                        choices=["16:9", "1:1", "9:16"],
                        value="16:9"
                    )

                # Advanced Options
                with gr.Accordion("⚙️ Advanced Settings", open=False):
                    text_negative_prompt = gr.Textbox(
                        label="Negative Prompt",
                        placeholder="What you don't want to see in the video...",
                        lines=2
                    )
                    with gr.Row():
                        text_seed = gr.Textbox(
                            label="Seed (Optional)",
                            placeholder="Random seed for reproducibility"
                        )
                        text_duration = gr.Radio(
                            label="⏱️ Duration",
                            choices=[5, 10],
                            value=5
                        )
                    with gr.Row():
                        text_audio_enabled = gr.Checkbox(
                            label="🎵 Enable Audio Generation",
                            value=True
                        )
                        text_audio_url = gr.Textbox(
                            label="🎧 Custom Audio URL",
                            placeholder="https://example.com/audio.mp3"
                        )
            
            # Image-to-Video inputs
            with gr.Group(visible=False) as image_group:
                gr.Markdown("### 🖼️ Image-to-Video Generation")
                
                with gr.Row():
                    image_file = gr.Image(
                        label="Upload Starting Image",
                        type="filepath",
                        height=300
                    )
                    with gr.Column():
                        image_prompt = gr.Textbox(
                            label="Guidance Prompt (Optional)",
                            placeholder="Describe the desired motion or style...",
                            lines=3
                        )
                        image_style = gr.Dropdown(
                            label="Style",
                            choices=style_choices,
                            value=style_choices[0] if style_choices else "Auto"
                        )

                # Advanced Options
                with gr.Accordion("⚙️ Advanced Settings", open=False):
                    with gr.Row():
                        image_duration = gr.Radio(
                            label="⏱️ Duration",
                            choices=[5, 10],
                            value=5
                        )
                        image_audio_enabled = gr.Checkbox(
                            label="🎵 Enable Audio Generation",
                            value=True
                        )
                    image_audio_url = gr.Textbox(
                        label="🎧 Custom Audio URL",
                        placeholder="https://example.com/audio.mp3"
                    )
            
            # Keyframe-to-Video inputs
            with gr.Group(visible=False) as keyframe_group:
                gr.Markdown("### 🎞️ Keyframe-to-Video Generation")
                
                with gr.Row():
                    start_frame_file = gr.Image(
                        label="Start Frame",
                        type="filepath",
                        height=250
                    )
                    end_frame_file = gr.Image(
                        label="End Frame",
                        type="filepath",
                        height=250
                    )
                
                with gr.Row():
                    keyframe_prompt = gr.Textbox(
                        label="Transition Guidance (Optional)",
                        placeholder="Describe the desired transition between frames...",
                        lines=2
                    )
                    keyframe_style = gr.Dropdown(
                        label="Style",
                        choices=style_choices,
                        value=style_choices[0] if style_choices else "Auto"
                    )
            
            # Hidden state for task tracking
            task_id_state = gr.State(value="")
            
            # Generation button and outputs
            with gr.Row():
                generate_btn = gr.Button("🎬 Generate Video", variant="primary", size="lg")
            
            with gr.Row():
                with gr.Column(scale=1):
                    status_output = gr.Textbox(label="Status", interactive=False, lines=4)
                with gr.Column(scale=2):
                    video_output = gr.Video(label="Generated Video", height=400)
            
            # Timer for polling task status (hidden, starts inactive)
            status_timer = gr.Timer(value=5, active=False)
            
            # Mode switching logic
            def update_visibility(mode):
                return (
                    gr.update(visible=(mode == "Text-to-Video")),
                    gr.update(visible=(mode == "Image-to-Video")),
                    gr.update(visible=(mode == "Keyframe-to-Video"))
                )
            
            mode_selector.change(
                update_visibility,
                inputs=[mode_selector],
                outputs=[text_group, image_group, keyframe_group]
            )
            
            # Async task submission - this is now non-blocking
            generate_btn.click(
                self.submit_task_handler,
                inputs=[
                    mode_selector,
                    # Text-to-Video inputs
                    text_prompt, text_model, text_style, text_aspect_ratio, 
                    text_negative_prompt, text_seed,
                    text_duration, text_audio_enabled, text_audio_url,
                    # Image-to-Video inputs
                    image_file, image_prompt, image_style,
                    image_duration, image_audio_enabled, image_audio_url,
                    # Keyframe-to-Video inputs
                    start_frame_file, end_frame_file, keyframe_prompt, keyframe_style
                ],
                outputs=[task_id_state, status_output, status_timer]
            )
            
            # Timer tick event - polls task status
            status_timer.tick(
                self.check_task_status_handler,
                inputs=[task_id_state],
                outputs=[video_output, status_output, status_timer]
            )
            
            # Prompt Optimization event
            optimize_btn.click(
                optimize_prompt_with_qwen,
                inputs=[text_prompt],
                outputs=[text_prompt]
            )

            
            # Help section
            with gr.Accordion("ℹ️ Help & Information", open=False):
                gr.Markdown("""
                ### 📋 Generation Modes
                
                **Text-to-Video:** Generate videos from text descriptions
                - Processing time: 1-2 minutes
                - Supports multiple models and styles
                - Customizable aspect ratios and advanced settings
                
                **Image-to-Video:** Generate videos from a single starting image
                - Processing time: 7-10 minutes  
                - Uses advanced keyframe model
                - Optional text guidance for motion
                
                **Keyframe-to-Video:** Generate videos from start and end frames
                - Processing time: 7-10 minutes
                - Creates smooth transitions between frames
                - Optional text guidance for transition style
                
                ### 📏 Image Requirements
                - Formats: JPEG, PNG, BMP, WEBP
                - File size: Maximum 10MB
                - Dimensions: 360px to 2000px (width and height)
                
                ### ⚡ Tips for Better Results
                - Use detailed, specific descriptions
                - Include style keywords (cinematic, realistic, animated)
                - For keyframes, ensure similar composition between start/end frames
                - Be patient with longer processing times for image/keyframe modes
                """)
        
        return interface
    
    def launch(
        self,
        server_name: str = "127.0.0.1",
        server_port: int = 7860,
        share: bool = False,
        debug: bool = False
    ) -> None:
        """
        Launch the Gradio application.
        
        Args:
            server_name: Server host name
            server_port: Server port number
            share: Whether to create a public link
            debug: Whether to run in debug mode
        """
        interface = self.create_interface()
        
        logger.info(f"Launching Enhanced Gradio app on {server_name}:{server_port}")
        
        try:
            interface.launch(
                server_name=server_name,
                server_port=server_port,
                share=share,
                debug=debug,
                show_error=True,
                quiet=True
            )
        except Exception as e:
            if "localhost is not accessible" in str(e) or "shareable link must be created" in str(e):
                logger.warning("Localhost not accessible, creating shareable link...")
                interface.launch(
                    server_name=server_name,
                    server_port=server_port,
                    share=True,
                    debug=debug,
                    show_error=True,
                    quiet=True
                )
            else:
                raise

def create_app() -> "EnhancedGradioVideoApp":
    """
    Factory function to create the Enhanced Gradio application.
    
    Returns:
        EnhancedGradioVideoApp: Configured application instance
    """
    return EnhancedGradioVideoApp()

# Default interface creation for direct import
def create_interface() -> gr.Blocks:
    """Create the default enhanced Gradio interface."""
    app = create_app()
    return app.create_interface()

# Maintain backward compatibility
class GradioTextToVideoApp:
    """Legacy class for backward compatibility."""
    
    def __init__(self):
        self.app = EnhancedGradioVideoApp()
        logger.warning("GradioTextToVideoApp is deprecated. Use EnhancedGradioVideoApp instead.")
    
    def create_interface(self):
        return self.app.create_interface()
    
    def launch(self, **kwargs):
        return self.app.launch(**kwargs)