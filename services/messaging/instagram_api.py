"""Instagram API client for direct messaging."""

import os
import json
import aiohttp
import asyncio
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Use friend's environment variables
ACCESS_TOKEN = os.getenv("IG_TOKEN")
BUSINESS_ACCOUNT_ID = os.getenv("IG_USER_ID")

logger = logging.getLogger(__name__)


async def send_reply(sender_id: str, message_text: str) -> Dict:
    """
    Send a reply to an Instagram user using Instagram Graph API.
    
    Args:
        sender_id: Instagram user ID to send message to
        message_text: Message text to send
        
    Returns:
        dict: API response with success/error info
    """
    try:
        original_length = len(message_text)
        
        # Log original message details
        logger.info(f"[SEND_REQUEST] Attempting to send message to user {sender_id}")
        logger.debug(f"[SEND_REQUEST] Original message length: {original_length} chars")
        logger.debug(f"[SEND_REQUEST] Message preview: {message_text[:200]}..." if len(message_text) > 200 else f"[SEND_REQUEST] Full message: {message_text}")
        
        # Truncate message if too long (Instagram DM limit: 1000 chars)
        if len(message_text) > 1000:
            # Find last complete sentence within limit
            truncated = message_text[:950]  # Leave room for ellipsis
            last_sentence = max(
                truncated.rfind('.'),
                truncated.rfind('!'),
                truncated.rfind('?')
            )
            if last_sentence > 500:  # Only truncate at sentence if reasonable
                message_text = message_text[:last_sentence + 1] + "..."
            else:
                message_text = truncated + "..."
            
            logger.warning(f"[TRUNCATE] Message truncated for user {sender_id}")
            logger.warning(f"[TRUNCATE] Original: {original_length} chars → Final: {len(message_text)} chars")
            logger.debug(f"[TRUNCATE] Truncated message: {message_text}")
        
        # Use Instagram Graph API endpoint (friend's pattern)
        url = f"https://graph.instagram.com/v22.0/{BUSINESS_ACCOUNT_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "recipient": {"id": sender_id},
            "message": {"text": message_text}
        }
        
        # Log API request details
        logger.debug(f"[API_REQUEST] URL: {url}")
        logger.debug(f"[API_REQUEST] Headers: {dict(headers)}")
        logger.debug(f"[API_REQUEST] Data: {data}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                
                # Enhanced response logging
                if response.status == 200:
                    logger.info(f"[SEND_SUCCESS] Message sent to user {sender_id}")
                    logger.info(f"[SEND_SUCCESS] Response: {result}")
                    logger.debug(f"[SEND_SUCCESS] Final message length: {len(message_text)} chars")
                    return {"success": True, "result": result, "status_code": response.status}
                else:
                    logger.error(f"[SEND_FAILED] Failed to send message to user {sender_id}")
                    logger.error(f"[SEND_FAILED] Status: {response.status}")
                    logger.error(f"[SEND_FAILED] Error response: {result}")
                    logger.error(f"[SEND_FAILED] Message that failed: {message_text[:100]}...")
                    
                    # Log specific error types
                    if result.get('error'):
                        error_details = result['error']
                        logger.error(f"[SEND_FAILED] Error code: {error_details.get('code')}")
                        logger.error(f"[SEND_FAILED] Error type: {error_details.get('type')}")
                        logger.error(f"[SEND_FAILED] Error message: {error_details.get('message')}")
                        logger.error(f"[SEND_FAILED] Error subcode: {error_details.get('error_subcode')}")
                    
                    return {"error": result, "status_code": response.status}
                
    except Exception as e:
        logger.error(f"[SEND] Exception sending reply to user {sender_id}: {str(e)}")
        return {"error": str(e), "status_code": 500}


async def send_quick_replies(sender_id: str, message_text: str, quick_replies: list) -> Dict:
    """
    Send a message with quick reply buttons.
    
    Args:
        sender_id: Instagram user ID
        message_text: Message text
        quick_replies: List of quick reply options
        
    Returns:
        dict: API response
    """
    try:
        url = f"https://graph.instagram.com/v22.0/{BUSINESS_ACCOUNT_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Format quick replies
        formatted_replies = []
        for reply in quick_replies[:13]:  # Instagram limit is 13 quick replies
            formatted_replies.append({
                "content_type": "text",
                "title": reply.get("title", "")[:20],  # 20 char limit
                "payload": reply.get("payload", "")
            })
        
        data = {
            "recipient": {"id": sender_id},
            "message": {
                "text": message_text,
                "quick_replies": formatted_replies
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                
                logger.info(f"[SEND] Quick replies sent to {sender_id}: {result}")
                
                if response.status != 200:
                    logger.error(f"[SEND] Error sending quick replies: {result}")
                    return {"error": result, "status_code": response.status}
                    
                return {"success": True, "result": result, "status_code": response.status}
                
    except Exception as e:
        logger.error(f"[SEND] Exception sending quick replies: {str(e)}")
        return {"error": str(e), "status_code": 500}


async def send_image(sender_id: str, image_url: str) -> Dict:
    """
    Send an image to Instagram user.
    
    Args:
        sender_id: Instagram user ID
        image_url: URL of image to send
        
    Returns:
        dict: API response
    """
    try:
        url = f"https://graph.instagram.com/v22.0/{BUSINESS_ACCOUNT_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "recipient": {"id": sender_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": image_url,
                        "is_reusable": True
                    }
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                
                logger.info(f"[SEND] Image sent to {sender_id}: {result}")
                
                if response.status != 200:
                    logger.error(f"[SEND] Error sending image: {result}")
                    return {"error": result, "status_code": response.status}
                    
                return {"success": True, "result": result, "status_code": response.status}
                
    except Exception as e:
        logger.error(f"[SEND] Exception sending image: {str(e)}")
        return {"error": str(e), "status_code": 500}


async def get_account_info() -> Dict:
    """
    Get Instagram account information to verify credentials.
    
    Returns:
        dict: Account info or error
    """
    try:
        url = f"https://graph.instagram.com/v22.0/{BUSINESS_ACCOUNT_ID}"
        params = {
            "fields": "username,name,id",
            "access_token": ACCESS_TOKEN
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"Account info retrieved: {result}")
                    return {"success": True, "data": result}
                else:
                    logger.error(f"Error getting account info: {result}")
                    return {"error": result, "status_code": response.status}
                    
    except Exception as e:
        logger.error(f"Exception getting account info: {str(e)}")
        return {"error": str(e), "status_code": 500}


# Test function
async def test_credentials():
    """Test Instagram API credentials."""
    print(f"🧪 Testing Instagram API credentials...")
    print(f"📱 ACCESS_TOKEN: {ACCESS_TOKEN[:20] if ACCESS_TOKEN else 'None'}...")
    print(f"🆔 BUSINESS_ACCOUNT_ID: {BUSINESS_ACCOUNT_ID}")
    
    result = await get_account_info()
    if result.get("success"):
        data = result["data"]
        print(f"✅ Credentials valid!")
        print(f"   Username: @{data.get('username', 'N/A')}")
        print(f"   Name: {data.get('name', 'N/A')}")
        print(f"   ID: {data.get('id', 'N/A')}")
        return True
    else:
        print(f"❌ Credentials invalid: {result}")
        return False


if __name__ == "__main__":
    asyncio.run(test_credentials())