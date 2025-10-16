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
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/get",
                    params={
                        "user_id": str(user_id),  # Convert to string
                        "msg": msg,
                        "num_chats": num_chats,
                        "include_chat_history": "false"
                    },
                    headers={"accept": "application/json"}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error getting memories: {e}")
                return {"data": ""}
    
    async def add_memory(self, user_id: int, user_message: str, ai_message: str) -> dict:
        """Add conversation to memory"""
        async with httpx.AsyncClient() as client:
            try:
                # Try as JSON first (most APIs prefer this)
                response = await client.post(
                    f"{self.base_url}/add",
                    json={
                        "user_id": str(user_id),  # Convert to string
                        "user_message": user_message,
                        "ai_message": ai_message
                    },
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 422:
                    # If JSON fails, try form data
                    logger.warning("JSON request failed, trying form data")
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
                        return response.json()
                    except Exception as e2:
                        logger.error(f"Error adding memory with form data: {e2}")
                        return {}
                else:
                    logger.error(f"Error adding memory: {e}")
                    return {}
            except Exception as e:
                logger.error(f"Error adding memory: {e}")
                return {}
