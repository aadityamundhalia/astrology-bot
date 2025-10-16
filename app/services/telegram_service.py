from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

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
    
    async def send_message(self, chat_id: int, text: str):
        """Send text message to user"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    def setup_application(self, message_handler):
        """Setup telegram application with message handler"""
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )
        return self.application
