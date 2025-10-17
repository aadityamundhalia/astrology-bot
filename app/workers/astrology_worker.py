"""Worker that processes astrology requests from the queue"""
import logging
import asyncio
import re

from app.database import AsyncSessionLocal
from app.models import User

logger = logging.getLogger(__name__)

class AstrologyWorker:
    def __init__(
        self,
        telegram_service,
        memory_service,
        astrology_service,
        rudie_agent
    ):
        self.telegram_service = telegram_service
        self.memory_service = memory_service
        self.astrology_service = astrology_service
        self.rudie_agent = rudie_agent
    
    async def process_request(self, request_data: dict):
        """Process a single astrology request"""
        try:
            # Validate required fields
            required_fields = ['user_id', 'chat_id', 'message', 'user_context']
            missing_fields = [field for field in required_fields if field not in request_data]
            
            if missing_fields:
                logger.warning(f"⚠️ Skipping malformed message - missing fields: {missing_fields}")
                logger.debug(f"Message data: {request_data}")
                return  # Skip this message
            
            # Validate user_context
            required_context = ['name', 'date_of_birth', 'time_of_birth', 'place_of_birth']
            user_context = request_data.get('user_context', {})
            missing_context = [field for field in required_context if field not in user_context]
            
            if missing_context:
                logger.warning(f"⚠️ Skipping message - missing user context: {missing_context}")
                return
            
            user_id = request_data['user_id']
            chat_id = request_data['chat_id']
            text = request_data['message']
            request_id = request_data.get('request_id', 'unknown')
            
            # Skip test messages
            if isinstance(text, str) and ('test' in text.lower() or 'batch_test' in text.lower()):
                logger.info(f"⏭️ Skipping test message: {request_id}")
                return
            
            # Send typing indicator
            stop_typing = asyncio.Event()
            typing_task = asyncio.create_task(
                self.telegram_service.keep_typing(chat_id, stop_typing)
            )
            
            try:
                logger.info(f"🔮 Processing astrology query for user {user_id}")
                
                # Get memories
                try:
                    memories_result = await self.memory_service.get_memories(user_id, text)
                    memory_data = ""
                    
                    if memories_result and isinstance(memories_result, dict):
                        memory_data = memories_result.get("data", "")
                    else:
                        logger.warning(f"🧠 Invalid memories result: {type(memories_result)}")
                        memory_data = ""
                        
                except Exception as e:
                    logger.warning(f"🧠 Failed to get memories, continuing without: {e}")
                    memory_data = ""
                
                # Add memories to context
                user_context['memories'] = memory_data
                
                # Generate response using Rudie agent
                response = await self.rudie_agent.generate_response(
                    user_message=text,
                    user_context=user_context,
                    astrology_service=self.astrology_service
                )
                
                # Clean response
                response = re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL)
                response = response.strip()
                
                # Stop typing
                stop_typing.set()
                if typing_task:
                    await typing_task
                
                # Send response
                await self.telegram_service.send_message(chat_id, response)
                
                # Save to database and Redis
                async with AsyncSessionLocal() as db:
                    await self.telegram_service.save_chat_to_db(db, user_id, "user", text)
                    await self.telegram_service.save_chat_to_db(db, user_id, "bot", response)
                
                self.telegram_service.save_chat_to_redis(user_id, "user", text)
                self.telegram_service.save_chat_to_redis(user_id, "bot", response)
                
                # Add to memory (in background)
                async def add_memory_safe():
                    try:
                        await self.memory_service.add_memory(user_id, text, response)
                    except Exception as e:
                        logger.error(f"Failed to add memory: {e}")
                
                asyncio.create_task(add_memory_safe())
                
                logger.info(f"✅ Completed request {request_id} for user {user_id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing request {request_id}: {e}", exc_info=True)
                
                stop_typing.set()
                if typing_task:
                    try:
                        await typing_task
                    except:
                        pass
                
                try:
                    await self.telegram_service.send_message(
                        chat_id,
                        "Sorry, I had trouble reading the stars for you. Please try again! 🌿"
                    )
                except:
                    pass
            finally:
                stop_typing.set()
                if typing_task and not typing_task.done():
                    try:
                        await typing_task
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"❌ Fatal error in process_request: {e}", exc_info=True)