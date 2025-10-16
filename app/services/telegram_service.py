from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler, ConversationHandler
from config import get_settings
import logging
import asyncio
import redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ChatHistory
from datetime import datetime

logger = logging.getLogger(__name__)
settings = get_settings()

# Telegram message length limit
TELEGRAM_MAX_LENGTH = 4096

# Conversation states
BIRTH_DATE, BIRTH_TIME, BIRTH_PLACE = range(3)

class TelegramService:
    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.application = None
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True
        )
    
    async def send_typing(self, chat_id: int):
        """Send typing indicator to show bot is processing"""
        try:
            await self.bot.send_chat_action(chat_id=chat_id, action="typing")
        except Exception as e:
            logger.error(f"Error sending typing action: {e}")
    
    async def keep_typing(self, chat_id: int, stop_event: asyncio.Event):
        """Keep sending typing indicator until stop_event is set"""
        try:
            while not stop_event.is_set():
                await self.send_typing(chat_id)
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=4.0)
                except asyncio.TimeoutError:
                    continue
        except Exception as e:
            logger.error(f"Error in keep_typing: {e}")
    
    async def send_message(self, chat_id: int, text: str, reply_markup=None):
        """Send text message to user with length validation"""
        try:
            if len(text) > TELEGRAM_MAX_LENGTH:
                logger.warning(f"Message too long ({len(text)} chars), truncating...")
                text = text[:TELEGRAM_MAX_LENGTH-50] + "\n\n✨ (Message truncated)"
            
            await self.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
            logger.info(f"📤 Telegram sent: chat {chat_id} - {len(text)} chars")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="Sorry, I generated too much info! 🌙 Could you ask about something more specific? 🌿"
                )
            except:
                pass
            raise
    
    def setup_application(self, message_handler, conversation_handler, clear_handler, start_handler=None, help_handler=None, info_handler=None):
        """Setup telegram application with message and command handlers"""
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        
        # Add command handlers
        if start_handler:
            self.application.add_handler(CommandHandler("start", start_handler))
        
        if help_handler:
            self.application.add_handler(CommandHandler("help", help_handler))
        
        if info_handler:
            self.application.add_handler(CommandHandler("info", info_handler))
        
        # Add conversation handler for birth details (BEFORE clear and message handlers)
        self.application.add_handler(conversation_handler)
        
        self.application.add_handler(CommandHandler("clear", clear_handler))
        
        # Add message handler (must be last)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )
        
        return self.application
    
    async def save_chat_to_db(self, db: AsyncSession, user_id: int, message_type: str, message: str):
        """Save chat message to database"""
        try:
            chat_entry = ChatHistory(
                user_id=user_id,
                message_type=message_type,
                message=message,
                timestamp=datetime.utcnow()
            )
            db.add(chat_entry)
            await db.commit()
        except Exception as e:
            logger.error(f"Error saving chat to DB: {e}")
    
    def save_chat_to_redis(self, user_id: int, message_type: str, message: str):
        """Save chat to Redis with sliding window limit"""
        try:
            key = f"chat_history:{user_id}"
            history = self.redis_client.lrange(key, 0, -1)
            
            pairs = []
            for i in range(0, len(history), 2):
                if i + 1 < len(history):
                    pairs.append((history[i], history[i+1]))
            
            if message_type == "user":
                pairs.append((message, ""))
            elif message_type == "bot" and pairs:
                last_pair = list(pairs[-1])
                last_pair[1] = message
                pairs[-1] = tuple(last_pair)
            
            pairs = pairs[-settings.redis_chat_history_limit:]
            
            self.redis_client.delete(key)
            for user_msg, bot_msg in pairs:
                self.redis_client.rpush(key, user_msg)
                if bot_msg:
                    self.redis_client.rpush(key, bot_msg)
                    
        except Exception as e:
            logger.error(f"Error saving chat to Redis: {e}")
    
    async def clear_user_history(self, db: AsyncSession, user_id: int):
        """Clear user's chat history from DB and Redis"""
        try:
            await db.execute(f"DELETE FROM chat_history WHERE user_id = {user_id}")
            await db.commit()
            
            key = f"chat_history:{user_id}"
            self.redis_client.delete(key)
            
            logger.info(f"🗑️ Cleared chat history for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing history for user {user_id}: {e}")
    
    async def get_chat_history_from_redis(self, user_id: int) -> list:
        """Get chat history from Redis"""
        try:
            key = f"chat_history:{user_id}"
            history = self.redis_client.lrange(key, 0, -1)
            return history
        except Exception as e:
            logger.error(f"Error getting chat history from Redis: {e}")
            return []