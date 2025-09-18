"""
Instagram Image Download and Processing
Handles downloading and processing images from Instagram webhooks
"""

import asyncio
import aiohttp
import structlog
from typing import Optional, Tuple, Dict, Any
import os

logger = structlog.get_logger()

class InstagramImageHandler:
    """Handle Instagram image attachments for prescription analysis."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.ig_token = os.getenv("IG_TOKEN")
        
    async def download_image_from_attachment(self, attachment: Dict[str, Any]) -> Optional[Tuple[bytes, str]]:
        """
        Download image from Instagram attachment.
        
        Args:
            attachment: Instagram attachment dict with 'type' and 'payload' fields
            
        Returns:
            Tuple of (image_bytes, image_format) or None if failed
        """
        try:
            if attachment.get("type") != "image":
                self.logger.warning(f"Attachment is not an image: {attachment.get('type')}")
                return None
            
            payload = attachment.get("payload", {})
            image_url = payload.get("url")
            
            if not image_url:
                self.logger.error("No URL found in image attachment payload")
                return None
            
            self.logger.info(f"📷 Downloading image from Instagram: {image_url[:50]}...")
            
            # Download image using Instagram Graph API
            headers = {
                "Authorization": f"Bearer {self.ig_token}",
                "User-Agent": "Krsnaa Diagnostics Bot/1.0"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(image_url, headers=headers) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Determine image format from content type or URL
                        content_type = response.headers.get('content-type', '').lower()
                        image_format = self._determine_image_format(content_type, image_url)
                        
                        self.logger.info(f"✅ Successfully downloaded image", 
                                       size_bytes=len(image_data), 
                                       format=image_format,
                                       content_type=content_type)
                        
                        return image_data, image_format
                    else:
                        self.logger.error(f"Failed to download image: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error downloading Instagram image: {e}")
            return None
    
    def _determine_image_format(self, content_type: str, url: str) -> str:
        """Determine image format from content type or URL."""
        # Check content type first
        if 'jpeg' in content_type or 'jpg' in content_type:
            return 'jpeg'
        elif 'png' in content_type:
            return 'png'
        elif 'webp' in content_type:
            return 'webp'
        elif 'gif' in content_type:
            return 'gif'
        
        # Fall back to URL extension
        url_lower = url.lower()
        if url_lower.endswith(('.jpg', '.jpeg')):
            return 'jpeg'
        elif url_lower.endswith('.png'):
            return 'png'
        elif url_lower.endswith('.webp'):
            return 'webp'
        elif url_lower.endswith('.gif'):
            return 'gif'
        
        # Default to jpeg
        return 'jpeg'
    
    async def process_prescription_images(self, attachments: list) -> Optional[Tuple[bytes, str]]:
        """
        Process multiple attachments and return the first valid prescription image.
        
        Args:
            attachments: List of Instagram attachment objects
            
        Returns:
            Tuple of (image_bytes, image_format) for the first valid prescription image
        """
        if not attachments:
            return None
        
        for attachment in attachments:
            try:
                result = await self.download_image_from_attachment(attachment)
                if result:
                    image_data, image_format = result
                    
                    # Basic validation - ensure it's a reasonable size for prescription
                    if len(image_data) > 50000:  # At least 50KB for a meaningful prescription image
                        self.logger.info(f"📋 Found valid prescription image candidate", 
                                       format=image_format, size_kb=len(image_data)//1024)
                        return result
                    else:
                        self.logger.warning(f"Image too small for prescription: {len(image_data)} bytes")
                        
            except Exception as e:
                self.logger.error(f"Error processing attachment: {e}")
                continue
        
        self.logger.warning("No valid prescription images found in attachments")
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
            self.logger.error(f"Error checking image format: {e}")
            return False


# Global instance
_global_image_handler = None

def get_instagram_image_handler() -> InstagramImageHandler:
    """Get or create global Instagram image handler instance."""
    global _global_image_handler
    if _global_image_handler is None:
        _global_image_handler = InstagramImageHandler()
        logger.info("📷 Created Instagram image handler for prescription processing")
    return _global_image_handler