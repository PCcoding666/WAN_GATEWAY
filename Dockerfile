# Use Python 3.11 slim image for optimal size and compatibility
FROM python:3.11-slim

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=7860

# Create application directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies with multiple mirrors and fallback capabilities
RUN pip install --no-cache-dir --upgrade pip --index-url https://pypi.tuna.tsinghua.edu.cn/simple || \
    pip install --no-cache-dir --upgrade pip --index-url https://mirrors.aliyun.com/pypi/simple/ || \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple || \
    pip install --no-cache-dir -r requirements.txt --index-url https://mirrors.aliyun.com/pypi/simple/ || \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY main.py .

# Create directories for application data
RUN mkdir -p /app/downloads /app/cache

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE $PORT

# Run the application
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "7860"]