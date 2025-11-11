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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedGradioVideoApp:
    """Enhanced Gradio application for multi-modal video generation."""
    
    def __init__(self):
        """Initialize the Enhanced Gradio application."""
        self.app = MultiModalVideoApp()
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
                with gr.Row():
                    with gr.Column(scale=2):
                        text_prompt = gr.Textbox(
                            label="Video Description",
                            placeholder="Describe the video you want to generate...",
                            lines=3
                        )
                        text_negative_prompt = gr.Textbox(
                            label="Negative Prompt (Optional)",
                            placeholder="What you don't want to see in the video...",
                            lines=2
                        )
                    with gr.Column(scale=1):
                        text_model = gr.Radio(
                            label="Model",
                            choices=text_model_choices,
                            value=text_model_choices[0] if text_model_choices else "Wanxiang 2.2 Pro"
                        )
                        text_style = gr.Dropdown(
                            label="Style",
                            choices=style_choices,
                            value=style_choices[0] if style_choices else "Auto"
                        )
                        text_aspect_ratio = gr.Radio(
                            label="Aspect Ratio",
                            choices=["16:9", "1:1", "9:16"],
                            value="16:9"
                        )
                        text_seed = gr.Textbox(
                            label="Seed (Optional)",
                            placeholder="Random seed for reproducibility"
                        )
                with gr.Row():
                    with gr.Column():
                        text_duration = gr.Radio(
                            label="⏱️ Video Duration (Wan 2.5 Only)",
                            choices=[5, 10],
                            value=5,
                            info="Duration in seconds"
                        )
                    with gr.Column():
                        text_audio_enabled = gr.Checkbox(
                            label="🎵 Enable Audio Generation (Wan 2.5 Only)",
                            value=True,
                            info="Automatically generate synchronized audio"
                        )
                with gr.Row():
                    text_audio_url = gr.Textbox(
                        label="🎧 Custom Audio URL (Optional, Wan 2.5 Only)",
                        placeholder="https://example.com/audio.mp3",
                        info="Provide a custom audio file URL"
                    )
            
            # Image-to-Video inputs
            with gr.Group(visible=False) as image_group:
                gr.Markdown("### 🖼️ Image-to-Video Generation")
                gr.Markdown("*Expected processing time: 7-10 minutes*")
                with gr.Row():
                    with gr.Column(scale=1):
                        image_file = gr.File(
                            label="Upload Starting Image",
                            file_types=["image"],
                            type="filepath"
                        )
                    with gr.Column(scale=1):
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
                with gr.Row():
                    with gr.Column():
                        image_duration = gr.Radio(
                            label="⏱️ Video Duration (Wan 2.5 Only)",
                            choices=[5, 10],
                            value=5,
                            info="Duration in seconds"
                        )
                    with gr.Column():
                        image_audio_enabled = gr.Checkbox(
                            label="🎵 Enable Audio Generation (Wan 2.5 Only)",
                            value=True,
                            info="Automatically generate synchronized audio"
                        )
                with gr.Row():
                    image_audio_url = gr.Textbox(
                        label="🎧 Custom Audio URL (Optional, Wan 2.5 Only)",
                        placeholder="https://example.com/audio.mp3",
                        info="Provide a custom audio file URL"
                    )
            
            # Keyframe-to-Video inputs
            with gr.Group(visible=False) as keyframe_group:
                gr.Markdown("### 🎞️ Keyframe-to-Video Generation")
                gr.Markdown("*Expected processing time: 7-10 minutes*")
                with gr.Row():
                    with gr.Column():
                        start_frame_file = gr.File(
                            label="Upload Start Frame",
                            file_types=["image"],
                            type="filepath"
                        )
                    with gr.Column():
                        end_frame_file = gr.File(
                            label="Upload End Frame",
                            file_types=["image"],
                            type="filepath"
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
            
            # Generation button and outputs
            with gr.Row():
                generate_btn = gr.Button("🎬 Generate Video", variant="primary", size="lg")
            
            with gr.Row():
                status_output = gr.Textbox(label="Status", interactive=False, lines=2)
                video_output = gr.Video(label="Generated Video", height=400)
            
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
            
            # Generation event
            generate_btn.click(
                self.generate_video_handler,
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
                outputs=[video_output, status_output]
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
                show_api=False,
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
                    show_api=False,
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