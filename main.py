#!/usr/bin/env python3
"""
Main entry point for the Gradio Bailian Text-to-Video Application.

This script provides a command-line interface to launch the web application
with various configuration options.
"""
import argparse
import logging
import sys
import os
from pathlib import Path
import socket

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from src.gradio_app import create_app, EnhancedGradioVideoApp
    from src.config import Config
    from src.video_service_factory import MultiModalVideoApp
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed by running:")
    print("pip install -r requirements.txt")
    sys.exit(1)

def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def find_available_port(start_port: int, end_port: int = 65535) -> int:
    """
    Find the first available port in a given range.

    Args:
        start_port: The port number to start searching from.
        end_port: The upper bound of the port range to search.

    Returns:
        The first available port number, or raises an IOError if no port is available.
    """
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    raise IOError(f"No available ports in range {start_port}-{end_port}")

def check_environment():
    """Check if the environment is properly configured."""
    try:
        # Validate configuration
        Config.validate_config()
        
        # Initialize multi-modal app
        app = MultiModalVideoApp(api_key=Config.DASHSCOPE_API_KEY)
        status = app.get_service_status()
        
        print("✅ Environment Check Passed")
        print(f"   API Configured: {status['api_configured']}")
        print(f"   Supported Modes: {', '.join(status['supported_modes'])}")
        print(f"   Current Mode: {status['current_mode'] or 'None'}")
        print("   Available Models:")
        for mode, info in status['modes_info'].items():
            print(f"     {mode}: {', '.join(info['available_models'])}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Environment check failed: {e}")
        print("\nPlease ensure:")
        print("1. DASHSCOPE_API_KEY is set in your .env file")
        print("2. All dependencies are installed (pip install -r requirements.txt)")
        print("3. You have internet connectivity")
        return False

def main():
    """Main function to run the application."""
    parser = argparse.ArgumentParser(
        description="Wan Gateway Studio — Wan 3.0 / 2.7 / 2.6 video generation UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Launch with default settings
  python main.py --port 8080              # Launch on port 8080
  python main.py --share                  # Create public link
  python main.py --debug                  # Enable debug mode
  python main.py --check-env              # Check environment only
        """
    )
    
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "127.0.0.1"),
        help="Host to bind the server to (default: $HOST or 127.0.0.1)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "7860")),
        help="Port to run the server on (default: $PORT or 7860)"
    )
    
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public link for the app"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging"
    )
    
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check environment configuration and exit"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview requests without calling DashScope (same as WAN_DRY_RUN=1)"
    )

    parser.add_argument(
        "--show-legacy",
        action="store_true",
        help="Also list Wan 2.2 / 2.5 models in the UI (same as WAN_SHOW_LEGACY=1)"
    )
    
    args = parser.parse_args()

    if args.dry_run:
        Config.DRY_RUN = True
    if args.show_legacy:
        Config.SHOW_LEGACY_MODELS = True
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    print("🎬 Wan Gateway Studio")
    print("=" * 50)
    
    # Check environment (skipped in dry-run so the UI can be explored without a key)
    if not Config.DRY_RUN and not check_environment():
        sys.exit(1)
    elif Config.DRY_RUN:
        print("🧪 Dry-run mode: no API calls will be made")
    
    # If only checking environment, exit here
    if args.check_env:
        print("Environment check completed successfully!")
        sys.exit(0)
    
    try:
        # Find an available port
        try:
            available_port = find_available_port(args.port)
            if available_port != args.port:
                print(f"⚠️ Port {args.port} is in use. Using port {available_port} instead.")
        except IOError as e:
            logger.error(f"Port search failed: {e}")
            print(f"❌ {e}")
            sys.exit(1)

        # Create and launch the application
        logger.info("Initializing Gradio application...")
        app = create_app()
        
        print(f"🚀 Starting server on {args.host}:{available_port}")
        if args.share:
            print("🌐 Creating public link...")
        if args.debug:
            print("🔍 Debug mode enabled")
        
        print("\n" + "=" * 50)
        print("Application is starting...")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Launch the application
        app.launch(
            server_name=args.host,
            server_port=available_port,
            share=args.share,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"\n❌ Failed to start application: {e}")
        
        if args.debug:
            import traceback
            traceback.print_exc()
        
        sys.exit(1)

if __name__ == "__main__":
    main()