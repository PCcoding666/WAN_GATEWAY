# 🚀 Vercel Deployment Guide for WAN_GATEWAY

This guide will help you deploy your Gradio Text-to-Video application to Vercel for public access.

## 📋 Prerequisites

- ✅ GitHub account
- ✅ Vercel account (sign up with GitHub at [vercel.com](https://vercel.com))
- ✅ DASHSCOPE_API_KEY from Alibaba Cloud

## 🔧 Project Structure for Vercel

Your project now includes the following Vercel-specific files:

```
WAN_GATEWAY/
├── api/
│   └── index.py          # Vercel serverless function entry point
├── vercel.json           # Vercel configuration
├── requirements.txt      # Updated with FastAPI dependencies
├── src/                  # Your application code
├── tests/               # Your tests
└── README.md            # This file
```

## 🌐 Step-by-Step Deployment

### 1. **Ensure Your Code is on GitHub**

Your code is already pushed to: https://github.com/PCcoding666/WAN_GATEWAY.git

### 2. **Login to Vercel**

1. Go to [vercel.com](https://vercel.com)
2. Click "Sign up" and choose "Continue with GitHub"
3. Authorize Vercel to access your GitHub repositories

### 3. **Create New Project**

1. In Vercel dashboard, click "Add New..." → "Project"
2. Find your `WAN_GATEWAY` repository
3. Click "Import"

### 4. **Configure Project Settings**

#### **Project Configuration:**
- **Project Name**: `wan-gateway` (or your preferred name)
- **Framework Preset**: `Other` (Vercel will auto-detect)
- **Root Directory**: `.` (leave default)

#### **Environment Variables (CRITICAL!):**
In the "Environment Variables" section, add:

| Name | Value |
|------|-------|
| `DASHSCOPE_API_KEY` | `sk-de69c9fda92a4fafabd5dae615e38866` |

**⚠️ Important**: Make sure to use your actual API key value.

### 5. **Deploy**

1. Click "Deploy"
2. Wait for the build process (2-3 minutes)
3. Your app will be available at: `https://your-project-name.vercel.app`

## 🔗 Access Your Application

After deployment, your application will be available at multiple endpoints:

- **Main Application**: `https://your-project-name.vercel.app/gradio`
- **Health Check**: `https://your-project-name.vercel.app/health`
- **Root Redirect**: `https://your-project-name.vercel.app/` (redirects to `/gradio`)

## 🛠️ Technical Details

### **How It Works**

1. **`vercel.json`**: Tells Vercel to use Python runtime and route all requests to `api/index.py`
2. **`api/index.py`**: Creates a FastAPI application and mounts your Gradio interface
3. **Environment Variables**: Vercel injects your API key as environment variables
4. **Serverless**: Each request spins up a serverless function instance

### **Performance Considerations**

- **Cold Starts**: First request after inactivity may take 10-30 seconds
- **Timeout**: Functions timeout after 5 minutes (configured in `vercel.json`)
- **Concurrent Users**: Vercel automatically scales based on demand

### **Cost Information**

- **Hobby Plan**: Free tier includes:
  - 100 GB-hours of function execution per month
  - 100 deployments per day
  - Custom domains

## 🔍 Troubleshooting

### **Common Issues**

1. **Build Failure**:
   - Check that all dependencies are listed in `requirements.txt`
   - Verify Python version compatibility

2. **Environment Variable Issues**:
   - Ensure `DASHSCOPE_API_KEY` is set in Vercel dashboard
   - Check for typos in variable name

3. **Import Errors**:
   - All imports are handled in `api/index.py` with proper path management

4. **Timeout Issues**:
   - Video generation may take 1-3 minutes
   - Function timeout is set to 5 minutes maximum

### **Checking Deployment Status**

1. Go to your Vercel dashboard
2. Click on your project
3. View deployment logs in the "Functions" tab
4. Check runtime logs for any errors

### **Testing Your Deployment**

1. **Health Check**: Visit `/health` endpoint to verify API configuration
2. **Interface**: Visit `/gradio` to access the full application
3. **Generate Video**: Try generating a short video to test full functionality

## 🔄 Continuous Deployment

Once deployed, any push to your GitHub repository's main branch will automatically trigger a new deployment on Vercel.

## 📞 Support

If you encounter issues:

1. Check Vercel deployment logs
2. Verify environment variables are set correctly
3. Test locally first using the same code structure
4. Check the GitHub repository for any recent changes

## 🎉 Success!

Once deployed, share your application URL with others to let them generate videos using your Gradio interface!

**Example URL**: `https://wan-gateway-chi.vercel.app/gradio`