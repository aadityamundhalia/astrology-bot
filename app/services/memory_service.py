import httpx
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class MemoryService:
    def __init__(self):
        self.base_url = settings.mem0_service_url
    
    async def get_memories(self, user_id: int, msg: str, num_chats: int = 10) -> dict:
        """Retrieve user memories"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/get",
                    params={
                        "user_id": user_id,  # Keep as int, not string
                        "msg": msg,
                        "num_chats": num_chats,
                        "include_chat_history": "false"
                    },
                    headers={"accept": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                logger.debug(f"Got memories for user {user_id}: {result}")
                return result
            except httpx.HTTPError as e:
                logger.error(f"HTTP error getting memories: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response body: {e.response.text}")
                return {"data": ""}
            except Exception as e:
                logger.error(f"Error getting memories: {e}", exc_info=True)
                return {"data": ""}
    
    async def add_memory(self, user_id: int, user_message: str, ai_message: str) -> dict:
        """Add conversation to memory"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Prepare payload exactly as documented
                payload = {
                    "user_id": user_id,  # Integer, not string
                    "user_message": user_message,
                    "ai_message": ai_message
                }
                
                logger.debug(f"Adding memory for user {user_id}, payload: {payload}")
                
                response = await client.post(
                    f"{self.base_url}/add",
                    json=payload,
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                logger.info(f"Memory added successfully for user {user_id}")
                return result
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Status error adding memory: {e}")
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
                logger.error(f"Request payload: {payload}")
                return {"status": "error", "message": str(e)}
                
            except httpx.RequestError as e:
                logger.error(f"Request error adding memory: {e}", exc_info=True)
                logger.error(f"Failed to connect to Mem0 service at {self.base_url}")
                return {"status": "error", "message": "Connection failed"}
                
            except Exception as e:
                logger.error(f"Unexpected error adding memory: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}