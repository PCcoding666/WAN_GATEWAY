#!/usr/bin/env python3
"""
Debug utility for testing video download functionality.
This script helps diagnose OSS connection issues.
"""
import requests
import os
import tempfile
import sys
from urllib.parse import urlparse

def test_download(url: str, max_retries: int = 3) -> bool:
    """Test downloading a video URL with comprehensive error handling."""
    print(f"Testing download from: {url[:100]}...")
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries}")
            
            # Create session with comprehensive headers
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site'
            })
            
            # Configure adapters for better connection handling
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Test connection first
            print("Testing HEAD request...")
            head_response = session.head(url, timeout=(10, 30))
            print(f"HEAD response: {head_response.status_code}")
            if head_response.status_code != 200:
                print(f"HEAD request failed: {head_response.status_code}")
                continue
            
            # Get file info
            content_length = head_response.headers.get('content-length')
            content_type = head_response.headers.get('content-type')
            print(f"Content-Length: {content_length}")
            print(f"Content-Type: {content_type}")
            
            # Download with streaming
            print("Starting download...")
            response = session.get(
                url,
                stream=True,
                timeout=(30, 120)
            )
            
            if response.status_code == 200:
                # Create temp file
                parsed_url = urlparse(url)
                file_extension = os.path.splitext(parsed_url.path)[1] or '.mp4'
                
                temp_dir = os.path.join(tempfile.gettempdir(), 'wan_gateway_debug')
                os.makedirs(temp_dir, exist_ok=True)
                
                local_path = os.path.join(temp_dir, f"debug_video{file_extension}")
                
                # Download
                downloaded_size = 0
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if downloaded_size % (1024 * 1024) == 0:  # Every MB
                                print(f"Downloaded: {downloaded_size / (1024*1024):.1f} MB")
                
                file_size = os.path.getsize(local_path)
                print(f"✅ Download successful!")
                print(f"File saved to: {local_path}")
                print(f"File size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
                return True
            else:
                print(f"❌ Download failed: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout on attempt {attempt + 1}")
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 Connection error on attempt {attempt + 1}: {str(e)}")
        except Exception as e:
            print(f"❌ Error on attempt {attempt + 1}: {str(e)}")
            
        if attempt < max_retries - 1:
            print("Retrying in 2 seconds...")
            import time
            time.sleep(2)
    
    print("❌ All download attempts failed")
    return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_download.py <video_url>")
        print("Example:")
        print("python debug_download.py 'https://dashscope-result-wlcb-acdr-1.oss-cn-wulanchabu-acdr-1.aliyuncs.com/...'")
        sys.exit(1)
    
    url = sys.argv[1]
    success = test_download(url)
    sys.exit(0 if success else 1)