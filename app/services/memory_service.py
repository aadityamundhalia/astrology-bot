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
                        "user_id": user_id,
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
                response = await client.post(
                    f"{self.base_url}/add",
                    data={
                        "user_id": user_id,
                        "user_message": user_message,
                        "ai_message": ai_message
                    },
                    headers={"accept": "application/json"}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error adding memory: {e}")
                return {}
