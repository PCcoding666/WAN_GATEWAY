"""
Gradio Web Interface for Bailian Text-to-Video Generation.

This module provides a user-friendly web interface for generating videos
from text descriptions using the Bailian wan-v1-t2v API.
"""
import gradio as gr
import os
import logging
from typing import Tuple, Optional
from .config import Config
from .text_to_video_service import TextToVideoService, VideoResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GradioTextToVideoApp:
    """Gradio application for text-to-video generation."""
    
    def __init__(self):
        """Initialize the Gradio application."""
        self.service = TextToVideoService()
        logger.info("Gradio Text-to-Video application initialized")
    
    def generate_video_handler(
        self,
        prompt: str,
        style: str,
        aspect_ratio: str,
        model: str,
        negative_prompt: Optional[str],
        seed: Optional[float]
    ) -> Tuple[Optional[str], str]:
        """
        Handle video generation request from Gradio interface.
        
        Args:
            prompt: Text description for video generation
            style: Selected video style
            aspect_ratio: Selected aspect ratio
            model: Selected model for generation
            negative_prompt: Optional negative prompt
            seed: Optional seed value
            
        Returns:
            Tuple[Optional[str], str]: (video_path, status_message)
        """
        try:
            # Convert seed to int if provided
            seed_int = None
            if seed is not None and seed != "":
                try:
                    seed_int = int(float(seed))
                except (ValueError, TypeError):
                    return None, "❌ Invalid seed value. Please enter a valid number."
            
            # Process negative prompt
            neg_prompt = negative_prompt.strip() if negative_prompt else None
            
            logger.info(f"Generating video with prompt: {prompt[:50]}...")
            
            # Call the service
            result: VideoResult = self.service.generate_video(
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio,
                model=model,
                negative_prompt=neg_prompt,
                seed=seed_int
            )
            
            if result.success:
                status_msg = f"✅ Video generated successfully in {result.generation_time:.1f}s"
                if result.task_id:
                    status_msg += f" (Task ID: {result.task_id})"
                
                # Prefer local video path for better stability, but handle fallback
                video_path = None
                if result.local_video_path and os.path.exists(result.local_video_path):
                    video_path = result.local_video_path
                    status_msg += " - Video downloaded locally"
                elif result.video_url:
                    video_path = result.video_url
                    status_msg += " - Using direct URL (download failed)"
                    logger.warning("Local download failed, using direct URL which may cause connection issues")
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
    
    def create_interface(self) -> gr.Interface:
        """
        Create a simple Gradio interface using gr.Interface to avoid JSON schema issues.
        
        Returns:
            gr.Interface: Basic Gradio interface
        """
        # Simple function that matches gr.Interface expectations
        def generate_video_simple(prompt, model, style, aspect_ratio):
            """
            Simple video generation function for gr.Interface.
            
            Args:
                prompt: Text description for video generation
                model: Selected model
                style: Selected video style
                aspect_ratio: Selected aspect ratio
                
            Returns:
                Tuple[str, str]: (status_message, video_url_or_none)
            """
            if not prompt or not prompt.strip():
                return "Please enter a video description", None
            
            # Debug logging
            logger.info(f"Interface inputs - prompt: {prompt[:30]}..., model: {model}, style: {style}, aspect_ratio: {aspect_ratio}")
            
            # Basic style mapping
            style_map = {
                "Auto": "<auto>", 
                "Cinematic": "Cinematic", 
                "Anime": "Anime",
                "Realistic": "Realistic"
            }
            
            # Model mapping (from display name to API name)
            model_map = {}
            for model_id, model_info in Config.MODEL_OPTIONS.items():
                model_map[model_info["name"]] = model_id
            
            api_style = style_map.get(style, "<auto>")
            api_model = model_map.get(model, "wan2.2-t2v-plus")
            
            try:
                # Generate video with model parameter
                result = self.generate_video_handler(
                    prompt, api_style, aspect_ratio, api_model, None, None
                )
                # Return status and video (gr.Interface expects this format)
                video_url = result[0] if result[0] else None
                status = result[1]
                return status, video_url
            except Exception as e:
                return f"Error: {str(e)}", None
        
        # Prepare model choices for display
        model_choices = []
        model_descriptions = []
        for model_id, model_info in Config.MODEL_OPTIONS.items():
            display_name = model_info["name"]
            description = model_info["description"]
            resolutions = ", ".join(model_info["resolutions"])
            framerate = model_info["framerate"]
            duration = model_info["duration"]
            
            model_choices.append(display_name)
            model_descriptions.append(f"{description} | Resolution: {resolutions} | Framerate: {framerate} | Duration: {duration}")
        
        # Create simple gr.Interface (older, more stable API)
        interface = gr.Interface(
            fn=generate_video_simple,
            inputs=[
                gr.Textbox(
                    label="Video Description",
                    placeholder="Describe the video you want to generate...",
                    lines=3
                ),
                gr.Radio(
                    label="Model",
                    choices=model_choices,
                    value=model_choices[0] if model_choices else "Wanxiang 2.2 Pro (Recommended)",
                    info="Choose the model for video generation"
                ),
                gr.Radio(
                    label="Style",
                    choices=["Auto", "Cinematic", "Anime", "Realistic"],
                    value="Auto",
                    info="Video generation style"
                ),
                gr.Radio(
                    label="Aspect Ratio",
                    choices=["16:9", "1:1", "9:16"],
                    value="16:9",
                    info="Video aspect ratio"
                )
            ],
            outputs=[
                gr.Textbox(label="Status"),
                gr.Video(label="Generated Video")
            ],
            title="🎬 Bailian Text-to-Video Generator",
            description="",
            theme="default"
        )
        
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
        
        logger.info(f"Launching Gradio app on {server_name}:{server_port}")
        
        try:
            interface.launch(
                server_name=server_name,
                server_port=server_port,
                share=share,
                debug=debug,
                show_error=True,
                show_api=False,  # Disable API documentation
                quiet=True  # Reduce verbose output
            )
        except Exception as e:
            # This fallback logic is useful for environments where localhost is not directly accessible
            if "localhost is not accessible" in str(e) or "shareable link must be created" in str(e):
                logger.warning("Localhost not accessible, creating shareable link...")
                interface.launch(
                    server_name=server_name,
                    server_port=server_port,
                    share=True,
                    debug=debug,
                    show_error=True,
                    show_api=False,  # Also disable API here
                    quiet=True
                )
            else:
                # Re-raise the exception if it's not the specific share link error
                raise

def create_app() -> "GradioTextToVideoApp":
    """
    Factory function to create the Gradio application.
    
    Returns:
        GradioTextToVideoApp: Configured application instance
    """
    return GradioTextToVideoApp()

# Default interface creation for direct import
def create_interface() -> gr.Interface:
    """Create the default Gradio interface."""
    app = create_app()
    return app.create_interface()