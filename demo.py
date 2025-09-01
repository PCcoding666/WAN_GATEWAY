#!/usr/bin/env python3
"""
Demo script for the Enhanced Multi-Modal Video Generator.

This script demonstrates the capabilities of all three generation modes
and provides examples of how to use the API programmatically.
"""
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.video_service_factory import VideoServiceFactory, MultiModalVideoApp
from src.config import Config

def demo_service_factory():
    """Demonstrate the VideoServiceFactory capabilities."""
    print("🎬 Enhanced Multi-Modal Video Generator Demo")
    print("=" * 50)
    
    print("\n📋 Supported Generation Modes:")
    for mode in VideoServiceFactory.get_supported_modes():
        print(f"  • {mode}: {VideoServiceFactory.get_mode_description(mode)}")
        
        models = VideoServiceFactory.get_mode_models(mode)
        default_model = VideoServiceFactory.get_default_model(mode)
        
        print(f"    Available models: {', '.join(models)}")
        print(f"    Default model: {default_model}")
        print()
    
    print("\n🔧 Service Factory Validation:")
    # Test validation
    valid_combinations = [
        ("text_to_video", "wan2.2-t2v-plus"),
        ("image_to_video", "wanx2.1-kf2v-plus"),
        ("keyframe_to_video", "wanx2.1-kf2v-plus")
    ]
    
    for mode, model in valid_combinations:
        error = VideoServiceFactory.validate_mode_and_model(mode, model)
        status = "✅ Valid" if error is None else f"❌ {error}"
        print(f"  {mode} + {model}: {status}")
    
    # Test invalid combination
    error = VideoServiceFactory.validate_mode_and_model("text_to_video", "wanx2.1-kf2v-plus")
    print(f"  text_to_video + wanx2.1-kf2v-plus: {'❌ ' + error if error else '✅ Valid'}")

def demo_multi_modal_app():
    """Demonstrate the MultiModalVideoApp capabilities."""
    print("\n🏗️ Multi-Modal Application Demo:")
    
    try:
        app = MultiModalVideoApp()
        status = app.get_service_status()
        
        print(f"  API Configured: {status['api_configured']}")
        print(f"  Current Mode: {status['current_mode'] or 'None (will be set on first use)'}")
        print(f"  Supported Modes: {len(status['supported_modes'])}")
        
        # Test mode switching
        print("\n🔄 Mode Switching Test:")
        for mode in ["text_to_video", "image_to_video", "keyframe_to_video"]:
            app.set_mode(mode)
            print(f"  Switched to: {app.current_mode}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def demo_configuration():
    """Demonstrate configuration capabilities."""
    print("\n⚙️ Configuration Demo:")
    
    print(f"  Max Prompt Length: {Config.MAX_PROMPT_LENGTH}")
    print(f"  Default Style: {Config.DEFAULT_STYLE}")
    print(f"  Default Aspect Ratio: {Config.DEFAULT_ASPECT_RATIO}")
    print(f"  Text-to-Video Polling Interval: {Config.POLLING_INTERVAL}s")
    print(f"  Keyframe Polling Interval: {Config.KEYFRAME_POLLING_INTERVAL}s")
    print(f"  Max Poll Time (Text): {Config.MAX_POLL_TIME}s")
    print(f"  Max Poll Time (Keyframe): {Config.KEYFRAME_MAX_POLL_TIME}s")
    
    print("\n📏 Image Upload Constraints:")
    img_config = Config.IMAGE_UPLOAD_CONFIG
    print(f"  Max file size: {img_config['max_size_mb']}MB")
    print(f"  Allowed formats: {', '.join(img_config['allowed_formats'])}")
    print(f"  Dimension range: {img_config['min_dimension']}-{img_config['max_dimension']}px")
    
    print("\n🎨 Style Options:")
    for i, style in enumerate(Config.STYLE_OPTIONS, 1):
        display_name = Config.get_style_display_name(style)
        print(f"  {i}. {display_name}")

def demo_api_endpoints():
    """Demonstrate API endpoint configuration."""
    print("\n🌐 API Endpoints:")
    print(f"  Text-to-Video: {Config.TEXT_TO_VIDEO_ENDPOINT}")
    print(f"  Keyframe-to-Video: {Config.KEYFRAME_VIDEO_ENDPOINT}")
    print(f"  Legacy (backward compatibility): {Config.API_ENDPOINT}")

def main():
    """Run all demonstrations."""
    try:
        demo_service_factory()
        demo_multi_modal_app()
        demo_configuration()
        demo_api_endpoints()
        
        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("\nNext steps:")
        print("  1. Set your DASHSCOPE_API_KEY in a .env file")
        print("  2. Run 'python main.py' to start the web interface")
        print("  3. Try all three generation modes!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()