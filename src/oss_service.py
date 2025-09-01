"""
OSS (Object Storage Service) upload functionality for image-to-video generation.
Uploads images to Alibaba Cloud OSS and returns public URLs.
"""

import os
import uuid
import time
import logging
from typing import Optional, Tuple
from PIL import Image
import oss2
from .config import Config

logger = logging.getLogger(__name__)

class OSSService:
    """OSS service for uploading images and getting public URLs."""
    
    def __init__(self):
        """Initialize OSS service with configuration."""
        if not Config.OSS_ENABLE:
            logger.warning("OSS is not fully configured. Using fallback to demo image.")
            self.enabled = False
            return
            
        self.enabled = True
        self.auth = oss2.Auth(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(self.auth, Config.OSS_ENDPOINT, Config.OSS_BUCKET_NAME)
        
        logger.info(f"OSS service initialized: {Config.OSS_BUCKET_NAME} at {Config.OSS_ENDPOINT}")
    
    def upload_image(self, image_file, image_info: dict = None) -> Tuple[Optional[str], Optional[dict]]:
        """
        Upload image to OSS and return public URL.
        
        Args:
            image_file: The uploaded image file from Gradio
            image_info: Optional image metadata
            
        Returns:
            tuple: (public_url, upload_info) or (None, None) if failed
        """
        if not self.enabled:
            # Return demo image URL as fallback
            demo_url = "https://cdn.translate.alibaba.com/r/wanx-demo-1.png"
            logger.info(f"OSS not configured, using demo image: {demo_url}")
            return demo_url, {"source": "demo", "url": demo_url}
        
        try:
            # Process and optimize the image
            processed_image, processed_info = self._process_image_for_upload(image_file)
            if not processed_image:
                logger.error("Failed to process image for upload")
                return None, None
            
            # Generate unique filename
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            file_extension = processed_info.get('format', 'jpg').lower()
            filename = f"images/{timestamp}_{unique_id}.{file_extension}"
            
            # Upload to OSS
            result = self.bucket.put_object(filename, processed_image)
            
            if result.status == 200:
                # Generate a signed URL for public access (valid for 24 hours)
                # This allows the API to access the image even though bucket is private
                try:
                    signed_url = self.bucket.sign_url('GET', filename, 24 * 3600)  # 24 hours
                    logger.info(f"Generated signed URL: {signed_url[:100]}...")
                except Exception as e:
                    logger.error(f"Failed to generate signed URL: {e}")
                    # Fallback: try to construct a direct URL and hope bucket allows it
                    signed_url = f"https://{Config.OSS_BUCKET_NAME}.{Config.OSS_ENDPOINT.replace('https://', '')}/{filename}"
                    logger.warning(f"Using direct URL as fallback: {signed_url[:100]}...")
                
                upload_info = {
                    "filename": filename,
                    "url": signed_url,
                    "size_bytes": processed_info.get('size_bytes', 0),
                    "format": processed_info.get('format', 'JPEG'),
                    "dimensions": f"{processed_info.get('width', 0)}x{processed_info.get('height', 0)}",
                    "upload_time": timestamp,
                    "etag": result.etag,
                    "access_type": "signed_url"
                }
                
                logger.info(f"Image uploaded successfully with signed URL: {filename}")
                return signed_url, upload_info
            else:
                logger.error(f"OSS upload failed with status: {result.status}")
                return None, None
                
        except Exception as e:
            logger.error(f"OSS upload error: {str(e)}")
            return None, None
    
    def _process_image_for_upload(self, image_file) -> Tuple[Optional[bytes], Optional[dict]]:
        """
        Process image for optimal upload to OSS.
        
        Args:
            image_file: The uploaded image file from Gradio
            
        Returns:
            tuple: (image_bytes, image_info) or (None, None) if failed
        """
        try:
            with Image.open(image_file) as img:
                # Get original image info
                width, height = img.size
                original_format = img.format or 'JPEG'
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (API prefers reasonable sizes)
                max_dimension = 1024  # Good balance for quality and file size
                if max(img.size) > max_dimension:
                    # Calculate new size maintaining aspect ratio
                    aspect_ratio = width / height
                    if width > height:
                        new_width = max_dimension
                        new_height = int(max_dimension / aspect_ratio)
                    else:
                        new_height = max_dimension
                        new_width = int(max_dimension * aspect_ratio)
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    width, height = img.size
                    logger.info(f"Image resized to: {width}x{height}")
                
                # Save as JPEG with good quality
                import io
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=90, optimize=True)
                image_bytes = buffer.getvalue()
                
                image_info = {
                    "width": width,
                    "height": height,
                    "format": "JPEG",
                    "size_bytes": len(image_bytes),
                    "original_format": original_format
                }
                
                logger.info(f"Image processed for upload: {width}x{height}, {len(image_bytes)} bytes")
                return image_bytes, image_info
                
        except Exception as e:
            logger.error(f"Error processing image for upload: {str(e)}")
            return None, None
    
    def cleanup_old_images(self, hours: int = 24):
        """
        Clean up old images from OSS bucket.
        
        Args:
            hours: Age threshold in hours for cleanup
        """
        if not self.enabled:
            return
        
        try:
            current_time = time.time()
            cutoff_time = current_time - (hours * 3600)
            
            # List objects in the images/ prefix
            objects = oss2.ObjectIterator(self.bucket, prefix='images/')
            
            deleted_count = 0
            for obj in objects:
                try:
                    # Extract timestamp from filename
                    filename_parts = obj.key.split('_')
                    if len(filename_parts) >= 2:
                        timestamp = int(filename_parts[0].split('/')[-1])
                        if timestamp < cutoff_time:
                            self.bucket.delete_object(obj.key)
                            deleted_count += 1
                            logger.debug(f"Deleted old image: {obj.key}")
                except (ValueError, IndexError):
                    # Skip files that don't match the expected naming pattern
                    continue
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old images from OSS")
                
        except Exception as e:
            logger.error(f"Error during OSS cleanup: {str(e)}")

# Global OSS service instance
oss_service = OSSService()