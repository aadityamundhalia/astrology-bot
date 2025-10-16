from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from config import get_settings
import logging
import asyncio

logger = logging.getLogger(__name__)
settings = get_settings()

# Telegram message length limit
TELEGRAM_MAX_LENGTH = 4096

class TelegramService:
    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.application = None
    
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
                # Wait 4 seconds before sending again (typing lasts 5 seconds)
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=4.0)
                except asyncio.TimeoutError:
                    continue
        except Exception as e:
            logger.error(f"Error in keep_typing: {e}")
    
    async def send_message(self, chat_id: int, text: str):
        """Send text message to user with length validation"""
        try:
            # Truncate if too long
            if len(text) > TELEGRAM_MAX_LENGTH:
                logger.warning(f"Message too long ({len(text)} chars), truncating...")
                text = text[:TELEGRAM_MAX_LENGTH-50] + "\n\n✨ (Message truncated)"
            
            await self.bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"📤 Telegram sent: chat {chat_id} - {len(text)} chars: {text[:100]}{'...' if len(text) > 100 else ''}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            # Try to send error message
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="Sorry, I generated too much info! 🌙 Could you ask about something more specific? Like 'how's today' or 'career this week'? 🌿"
                )
            except:
                pass
            raise
    
    def setup_application(self, message_handler):
        """Setup telegram application with message handler"""
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )
        return self.application
