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
                        "user_id": str(user_id),
                        "msg": msg,
                        "num_chats": num_chats,
                        "include_chat_history": "false"
                    },
                    headers={"accept": "application/json"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error getting memories: {e}")
                logger.error(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
                logger.error(f"Response body: {getattr(e.response, 'text', 'N/A')}")
                return {"data": ""}
            except Exception as e:
                logger.error(f"Error getting memories: {e}", exc_info=True)
                return {"data": ""}
    
    async def add_memory(self, user_id: int, user_message: str, ai_message: str) -> dict:
        """Add conversation to memory"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Try as JSON first (most APIs prefer this)
                logger.debug(f"Adding memory for user {user_id}")
                
                response = await client.post(
                    f"{self.base_url}/add",
                    json={
                        "user_id": str(user_id),
                        "user_message": user_message,
                        "ai_message": ai_message
                    },
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                logger.info(f"Memory added successfully for user {user_id}")
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Status error adding memory: {e}")
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
                
                if e.response.status_code == 422:
                    # If JSON fails, try form data
                    logger.warning("JSON request failed with 422, trying form data")
                    try:
                        response = await client.post(
                            f"{self.base_url}/add",
                            data={
                                "user_id": str(user_id),
                                "user_message": user_message,
                                "ai_message": ai_message
                            },
                            headers={"accept": "application/json"}
                        )
                        response.raise_for_status()
                        logger.info(f"Memory added successfully with form data for user {user_id}")
                        return response.json()
                    except Exception as e2:
                        logger.error(f"Error adding memory with form data: {e2}", exc_info=True)
                        return {}
                return {}
                
            except httpx.RequestError as e:
                logger.error(f"Request error adding memory: {e}", exc_info=True)
                logger.error(f"Failed to connect to Mem0 service at {self.base_url}")
                return {}
                
            except Exception as e:
                logger.error(f"Unexpected error adding memory: {e}", exc_info=True)
                return {}