"""
WhatsApp Image Download and Processing
Handles downloading and processing images from WhatsApp Business API webhooks
"""

import asyncio
import aiohttp
import structlog
from typing import Optional, Tuple, Dict, Any
import os
import base64

logger = structlog.get_logger()

class WhatsAppImageHandler:
    """Handle WhatsApp image messages for prescription analysis."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.access_token = os.getenv("WA_ACCESS_TOKEN")
        
    async def download_image_from_whatsapp_message(self, message_data: Dict[str, Any]) -> Optional[Tuple[bytes, str]]:
        """
        Download image from WhatsApp message data.
        
        Args:
            message_data: WhatsApp message data with image information
            
        Returns:
            Tuple of (image_bytes, image_format) or None if failed
        """
        try:
            # Check if this is an image message
            if message_data.get("type") != "image":
                self.logger.warning(f"Message is not an image: {message_data.get('type')}")
                return None
            
            # Extract image data from WhatsApp message
            image_info = message_data.get("image", {})
            media_id = image_info.get("id")
            
            if not media_id:
                self.logger.error("No media ID found in image message")
                return None
            
            self.logger.info(f"📷 Downloading WhatsApp image: {media_id}")
            
            # First, get the media URL from WhatsApp API
            media_url = await self._get_media_url(media_id)
            if not media_url:
                return None
            
            # Download the actual image data
            image_data = await self._download_media_file(media_url)
            if not image_data:
                return None
            
            # Determine image format
            image_format = self._determine_image_format_from_data(image_data)
            
            self.logger.info(f"✅ Successfully downloaded WhatsApp image", 
                           size_bytes=len(image_data), 
                           format=image_format)
            
            return image_data, image_format
            
        except Exception as e:
            self.logger.error(f"Error downloading WhatsApp image: {e}")
            return None
    
    async def _get_media_url(self, media_id: str) -> Optional[str]:
        """Get the actual media URL from WhatsApp API using media ID."""
        try:
            url = f"https://graph.facebook.com/v20.0/{media_id}"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": "Krsnaa Diagnostics Bot/1.0"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        media_info = await response.json()
                        media_url = media_info.get("url")
                        
                        if media_url:
                            self.logger.info(f"✅ Got WhatsApp media URL for {media_id}")
                            return media_url
                        else:
                            self.logger.error("No URL in WhatsApp media response")
                            return None
                    else:
                        error_data = await response.text()
                        self.logger.error(f"Failed to get WhatsApp media URL: HTTP {response.status} - {error_data}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error getting WhatsApp media URL: {e}")
            return None
    
    async def _download_media_file(self, media_url: str) -> Optional[bytes]:
        """Download the actual media file from WhatsApp CDN."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": "Krsnaa Diagnostics Bot/1.0"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.get(media_url, headers=headers) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Basic validation - ensure it's a reasonable size for prescription
                        if len(image_data) > 1000:  # At least 1KB
                            return image_data
                        else:
                            self.logger.warning(f"Downloaded image too small: {len(image_data)} bytes")
                            return None
                    else:
                        self.logger.error(f"Failed to download WhatsApp media: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error downloading WhatsApp media file: {e}")
            return None
    
    def _determine_image_format_from_data(self, image_data: bytes) -> str:
        """Determine image format from image data headers."""
        try:
            # Check magic bytes
            if image_data.startswith(b'\xff\xd8\xff'):
                return 'jpeg'
            elif image_data.startswith(b'\x89PNG'):
                return 'png'
            elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:20]:
                return 'webp'
            elif image_data.startswith(b'GIF8'):
                return 'gif'
            else:
                # Default to jpeg
                return 'jpeg'
                
        except Exception as e:
            self.logger.error(f"Error determining image format: {e}")
            return 'jpeg'
    
    async def process_whatsapp_image_message(self, message_data: Dict[str, Any]) -> Optional[Tuple[bytes, str]]:
        """
        Process WhatsApp image message and return image data if it's likely a prescription.
        
        Args:
            message_data: WhatsApp message data
            
        Returns:
            Tuple of (image_bytes, image_format) for prescription analysis
        """
        try:
            result = await self.download_image_from_whatsapp_message(message_data)
            if result:
                image_data, image_format = result
                
                # Process any image - let the AI determine if it's a prescription
                self.logger.info(f"📋 Processing WhatsApp image for analysis", 
                               format=image_format, size_kb=len(image_data)//1024)
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing WhatsApp image message: {e}")
            return None

    def is_likely_prescription(self, image_data: bytes) -> bool:
        """
        Basic heuristic to determine if image might be a prescription.
        This is a simple size and format check. The AI will do the real analysis.
        """
        try:
            # Basic size check - prescriptions are usually substantial images
            if len(image_data) < 10000:  # Less than 10KB probably not a prescription
                return False
                
            # Check if it starts with valid image headers
            if image_data.startswith(b'\xff\xd8\xff'):  # JPEG
                return True
            elif image_data.startswith(b'\x89PNG'):  # PNG
                return True
            elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:20]:  # WebP
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking WhatsApp image format: {e}")
            return False


# Global instance
_global_whatsapp_image_handler = None

def get_whatsapp_image_handler() -> WhatsAppImageHandler:
    """Get or create global WhatsApp image handler instance."""
    global _global_whatsapp_image_handler
    if _global_whatsapp_image_handler is None:
        _global_whatsapp_image_handler = WhatsAppImageHandler()
        logger.info("📷 Created WhatsApp image handler for prescription processing")
    return _global_whatsapp_image_handler