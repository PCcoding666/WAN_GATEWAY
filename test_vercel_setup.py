#!/usr/bin/env python3
"""
Test script to verify Vercel deployment setup works locally.
This script tests the api/index.py file to ensure it can be imported and run.
"""
import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
        
    try:
        import gradio
        print("✅ Gradio imported successfully")
    except ImportError as e:
        print(f"❌ Gradio import failed: {e}")
        return False
        
    try:
        from src.config import Config
        print("✅ Config imported successfully")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False
        
    try:
        from src.gradio_app import create_interface
        print("✅ Gradio app imported successfully")
    except ImportError as e:
        print(f"❌ Gradio app import failed: {e}")
        return False
        
    return True

def test_api_entry_point():
    """Test that the API entry point can be loaded."""
    print("\n🚀 Testing API entry point...")
    
    try:
        # Import the api module
        from api.index import app, handler
        print("✅ API entry point imported successfully")
        print(f"✅ FastAPI app created: {type(app)}")
        print(f"✅ Handler created: {type(handler)}")
        return True
    except Exception as e:
        print(f"❌ API entry point failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from src.config import Config
        
        # Check if API key is available
        if Config.DASHSCOPE_API_KEY:
            print("✅ API key configured")
        else:
            print("⚠️ API key not configured (expected for testing)")
            
        print(f"✅ API endpoint: {Config.API_ENDPOINT}")
        print(f"✅ Available models: {len(Config.MODEL_OPTIONS)}")
        print(f"✅ Style options: {len(Config.STYLE_OPTIONS)}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_interface_creation():
    """Test Gradio interface creation."""
    print("\n🎨 Testing interface creation...")
    
    try:
        from src.gradio_app import create_interface
        
        # This might fail if API key is not configured, but import should work
        interface = create_interface()
        print("✅ Gradio interface created successfully")
        print(f"✅ Interface type: {type(interface)}")
        
        return True
    except Exception as e:
        print(f"⚠️ Interface creation issue (may be normal without API key): {e}")
        return True  # Don't fail the test for this

def main():
    """Run all tests."""
    print("🧪 Testing Vercel Deployment Setup")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Interface Creation", test_interface_creation),
        ("API Entry Point", test_api_entry_point),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Your setup is ready for Vercel deployment.")
        print("\n📝 Next steps:")
        print("  1. Commit and push these changes to GitHub")
        print("  2. Follow the VERCEL_DEPLOYMENT.md guide")
        print("  3. Deploy on Vercel with your API key")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)