# 🧪 WAN Gateway Local Testing Guide

This guide provides comprehensive testing instructions for your WAN Gateway application without modifying any code.

## ✅ Prerequisites Check

All your environment prerequisites are properly set up:
- ✅ Virtual environment (`.venv`) exists
- ✅ Dependencies installed (Gradio 5.43.1, DashScope, etc.)
- ✅ Environment configuration ready (`.env` file)
- ✅ API key configured

## 🚀 Quick Start Testing

### Basic Launch
```bash
# Basic launch with default settings
.venv/bin/python main.py

# Launch with debug mode (recommended for testing)
.venv/bin/python main.py --debug

# Launch on specific port
.venv/bin/python main.py --port 8080

# Environment check only
.venv/bin/python main.py --check-env
```

## 🔧 Testing Scenarios

### 1. Environment Validation Test
```bash
.venv/bin/python main.py --check-env
```

**Expected Output:**
```
✅ Environment Check Passed
   API Configured: True
   API Endpoint: https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis
   Supported Styles: 7
   Supported Ratios: 3
```

### 2. Application Startup Test
```bash
.venv/bin/python main.py --debug --port 7862
```

**Expected Behavior:**
- Server starts successfully
- HTTP 200 response on the specified port
- Debug logs show initialization progress
- Gradio interface loads properly

### 3. Port Conflict Handling Test
```bash
# Start first instance
.venv/bin/python main.py --port 7860 &

# Start second instance (should auto-find next available port)
.venv/bin/python main.py --port 7860
```

**Expected Behavior:**
- Second instance automatically uses port 7861
- Warning message: "⚠️ Port 7860 is in use. Using port 7861 instead."

### 4. API Connectivity Test
```bash
# Test HTTP endpoint
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7862
```

**Expected Output:** `200`

## 🌐 Manual UI Testing

### Access the Application
1. Start the application: `.venv/bin/python main.py`
2. Open browser: `http://127.0.0.1:7860` (or displayed port)
3. Verify the interface loads properly

### Interface Component Tests

#### 1. Text Input Field
- **Test**: Enter various text prompts
- **Expected**: Text input accepts content without errors
- **Examples**:
  - "A beautiful sunset over mountains"
  - "A cat playing with a ball"
  - "City street at night with neon lights"

#### 2. Style Selection
- **Test**: Try different style options
- **Expected**: Dropdown shows all 7 supported styles
- **Styles**: Auto, Cinematic, Anime, Realistic, Abstract, Documentary, Commercial

#### 3. Aspect Ratio Selection
- **Test**: Select different aspect ratios
- **Expected**: Dropdown shows 3 options (16:9, 1:1, 9:16)

#### 4. Model Selection
- **Test**: Switch between different models
- **Expected**: 3 models available with different capabilities
- **Models**:
  - wan2.2-t2v-plus (1920×1080)
  - wanx2.1-t2v-turbo (1280×720)
  - wanx2.1-t2v-plus (832×480)

#### 5. Advanced Settings
- **Test**: Expand advanced settings section
- **Expected**: Shows negative prompt and seed fields
- **Features**:
  - Negative prompt input
  - Seed number input (optional)

### 5. Generation Test (If API Key Valid)
1. Enter prompt: "A peaceful lake at sunset"
2. Select style: "Cinematic"
3. Choose ratio: "16:9"
4. Click "Generate Video"
5. **Expected**: 
   - Progress indicator appears
   - Status updates show polling progress
   - Video displays when complete (or error message if API key invalid)

## 🔍 Command Line Options Testing

### Help Command
```bash
.venv/bin/python main.py --help
```

### Share Mode (Creates Public URL)
```bash
.venv/bin/python main.py --share
```
**Note**: Creates a temporary public URL for testing

### Host Binding Test
```bash
.venv/bin/python main.py --host 0.0.0.0 --port 7863
```
**Expected**: Accessible from other devices on the network

## 📊 Performance Testing

### Resource Usage Monitoring
```bash
# Monitor during startup
top -pid $(pgrep -f "python main.py")

# Memory usage
ps aux | grep "python main.py"
```

### Startup Time Test
```bash
time .venv/bin/python main.py --check-env
```

## 🐛 Troubleshooting Tests

### Missing Dependencies Test
```bash
# Temporarily rename .venv to test error handling
mv .venv .venv_backup
.venv/bin/python main.py
mv .venv_backup .venv
```

### Invalid API Key Test
```bash
# Backup current .env
cp .env .env.backup

# Create invalid API key
echo "DASHSCOPE_API_KEY=invalid_key" > .env

# Test environment check
.venv/bin/python main.py --check-env

# Restore valid .env
mv .env.backup .env
```

### Port Occupation Test
```bash
# Occupy port 7860
nc -l 7860 &
NC_PID=$!

# Try to start application
.venv/bin/python main.py --port 7860

# Clean up
kill $NC_PID
```

## 📝 Test Results Documentation

### Successful Test Indicators
- ✅ Environment check passes
- ✅ Server starts without errors
- ✅ HTTP 200 response
- ✅ Gradio interface loads
- ✅ All UI components render properly
- ✅ Port conflict handling works
- ✅ Debug logs show proper initialization

### Common Issues and Solutions

#### Issue: Import Errors
**Solution**: Ensure virtual environment is activated and dependencies installed
```bash
.venv/bin/pip install -r requirements.txt
```

#### Issue: Port Already in Use
**Expected Behavior**: Application automatically finds next available port

#### Issue: API Key Not Configured
**Solution**: Set proper API key in `.env` file
```bash
DASHSCOPE_API_KEY=your_actual_api_key_here
```

## 🎯 Testing Checklist

### Basic Functionality
- [ ] Environment check passes
- [ ] Application starts successfully
- [ ] Web interface loads
- [ ] All UI components visible
- [ ] Port conflict handling works
- [ ] Command line options function

### Advanced Features
- [ ] Video generation works (if API key valid)
- [ ] Progress tracking functions
- [ ] Error handling displays properly
- [ ] File downloads work
- [ ] Status indicators update correctly

### Performance
- [ ] Startup time under 10 seconds
- [ ] Memory usage reasonable
- [ ] No memory leaks during operation
- [ ] Responsive UI interaction

### Error Handling
- [ ] Graceful handling of invalid inputs
- [ ] Proper error messages display
- [ ] Recovery from network issues
- [ ] Clean shutdown with Ctrl+C

## 📋 Current Test Status

Based on the testing performed:

✅ **PASSED**: Environment validation
✅ **PASSED**: Application startup
✅ **PASSED**: HTTP endpoint response (200)
✅ **PASSED**: Port conflict detection
✅ **PASSED**: Debug mode logging
✅ **PASSED**: Command line argument parsing

**Your application is running successfully on:**
- **URL**: http://127.0.0.1:7862
- **Status**: HTTP 200 OK
- **Debug Mode**: Enabled
- **API Configuration**: Valid

## 🎉 Next Steps

1. **Access the application** in your browser: http://127.0.0.1:7862
2. **Test the UI components** manually
3. **Try video generation** (if you have a valid API key)
4. **Check logs** for any issues during operation

Your WAN Gateway application is ready for testing and use!