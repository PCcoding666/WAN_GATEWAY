"""
Vercel API entry point for Gradio Text-to-Video Application.

This module serves as the bridge between Vercel's serverless environment
and the Gradio application, using FastAPI as the ASGI application.
"""
import os
import sys
from pathlib import Path

# Add the project root and src directories to Python path
# This ensures that imports work correctly in Vercel's environment
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    import gradio as gr
    from fastapi import FastAPI
    from fastapi.responses import RedirectResponse
    
    # Import our application components
    from src.gradio_app import create_interface
    from src.config import Config
    
    # Initialize the Gradio interface
    def create_gradio_app():
        """Create and configure the Gradio interface for Vercel deployment."""
        try:
            # Create the interface using our existing function
            interface = create_interface()
            
            # Configure for cloud deployment
            interface.queue(default_enabled=True, max_size=20)
            
            return interface
        except Exception as e:
            # Create a simple error interface if main app fails
            def error_fn():
                return f"Application Error: {str(e)}"
            
            return gr.Interface(
                fn=error_fn,
                inputs=[],
                outputs=gr.Textbox(label="Error"),
                title="🚫 Application Error",
                description=f"Failed to initialize application: {str(e)}"
            )
    
    # Create FastAPI app
    app = FastAPI(
        title="WAN Gateway - Text-to-Video Generator",
        description="Gradio-based Text-to-Video Generator using Alibaba's Bailian API",
        version="1.0.0"
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        try:
            # Basic configuration check
            api_configured = bool(Config.DASHSCOPE_API_KEY)
            return {
                "status": "healthy",
                "api_configured": api_configured,
                "environment": "vercel"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "environment": "vercel"
            }
    
    # Redirect root to Gradio app
    @app.get("/")
    async def root():
        """Redirect root to Gradio interface."""
        return RedirectResponse(url="/gradio")
    
    # Create and mount the Gradio app
    gradio_app = create_gradio_app()
    
    # Mount Gradio app to FastAPI
    # The path="/gradio" means the Gradio interface will be available at /gradio
    app = gr.mount_gradio_app(app, gradio_app, path="/gradio")
    
except ImportError as e:
    # Fallback if there are import issues
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="Import Error")
    
    @app.get("/")
    async def import_error():
        return JSONResponse({
            "error": f"Import failed: {str(e)}",
            "message": "Please check dependencies and module paths"
        })

except Exception as e:
    # Ultimate fallback
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="Initialization Error")
    
    @app.get("/")
    async def init_error():
        return JSONResponse({
            "error": f"Initialization failed: {str(e)}",
            "message": "Application failed to start"
        })

# This is the ASGI application that Vercel will run
# Vercel's Python runtime expects this variable to be named 'app'
handler = app