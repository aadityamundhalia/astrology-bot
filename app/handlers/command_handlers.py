"""Command handlers for the Telegram bot"""
import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from sqlalchemy import select
import httpx

from config import get_settings
from app.database import AsyncSessionLocal
from app.models import User
from app.utils.validators import validate_birth_data

logger = logging.getLogger(__name__)
settings = get_settings()

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_service):
    """Handle /start command"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        has_birth_data = user and validate_birth_data(
            user.date_of_birth, 
            user.time_of_birth, 
            user.place_of_birth
        )
        
        if has_birth_data:
            welcome_message = f"""Hey {user.first_name}! 👋 Welcome back! 🌿

I've got your cosmic profile all set up. What would you like to know today?

You can ask me about:
- Today's energy - "How's today looking?"
- Weekly forecast - "What's my week like?"
- Career guidance - "Should I take this job offer?"
- Love insights - "Good time to ask them out?"
- Or anything else on your mind!

Need to update your details? Just type /change

Let's see what the stars have to say! ✨"""
        else:
            welcome_message = """Hi! I'm Rudie 🌿

I'm your friendly Vedic astrologer here to give you cosmic guidance! ✨

To get started, I'll need your birth details. You have two options:

**Option 1: Quick Setup (Wizard)** 
Just type /change and I'll guide you step-by-step!

**Option 2: All at Once**
Send your details in this format:

Date of Birth: 1990-01-15
Time of Birth: 10:30
Place of Birth: New Delhi, India

Once I have your details, you can ask me:
- "How is today for me?"
- "What's my week looking like?"
- "Tell me about my career this month"
- And much more!

Let's explore the stars together! 🌟"""
    
    await telegram_service.send_message(chat_id, welcome_message)

async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_service):
    """Handle /help command"""
    chat_id = update.effective_chat.id
    help_message = """🌿 **How to Use Rudie**

**Ask me about:**
📅 Daily predictions - "How's today?"
📆 Weekly forecasts - "What's my week like?"
💼 Career guidance - "Career outlook this month?"
💕 Love insights - "When should I propose?"
💰 Wealth timing - "Good time to invest?"
🏥 Health advice - "When to schedule surgery?"

**Commands:**
/start - Welcome & getting started
/help - Show this help message
/info - See your birth details
/change - Update birth details (wizard)
/clear - Clear chat history
/cancel - Cancel current operation

**Need More?**
Just ask naturally! I understand questions like:
- "Should I change jobs now?"
- "How are my relationships this quarter?"
- "What's my yearly forecast?"

Let the stars guide you! ✨"""
    
    await telegram_service.send_message(chat_id, help_message)

async def handle_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_service):
    """Handle /info command"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user and validate_birth_data(user.date_of_birth, user.time_of_birth, user.place_of_birth):
            info_message = f"""🌟 **Your Birth Details**

📅 Date of Birth: {user.date_of_birth}
🕐 Time of Birth: {user.time_of_birth}
📍 Place of Birth: {user.place_of_birth}

Your cosmic profile is all set up! ✨

Want to update? Type /change"""
        else:
            info_message = """❌ You haven't provided your birth details yet.

Type /change to set them up with the step-by-step wizard!

Or send them all at once in this format:

Date of Birth: 1990-01-15
Time of Birth: 10:30
Place of Birth: New Delhi, India"""
        
        await telegram_service.send_message(chat_id, info_message)

async def handle_clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_service):
    """Handle /clear command"""
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        logger.info(f"🗑️ Clear command received from user {user_id}")
        
        async with AsyncSessionLocal() as db:
            await telegram_service.clear_user_history(db, user_id)
            
            # Clear Mem0 memories
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.delete(
                        f"{settings.mem0_service_url}/clear",
                        params={"user_id": user_id}
                    )
                    if response.status_code == 200:
                        result = response.json()
                        message_count = result.get("message", "").split(" ")[1] if "messages" in result.get("message", "") else "unknown"
                        logger.info(f"🧠 Mem0 cleared: {message_count} messages for user {user_id}")
                    else:
                        logger.warning(f"🧠 Mem0 clear failed: HTTP {response.status_code}")
                except Exception as e:
                    logger.error(f"🧠 Mem0 clear error: {e}")
            
            response = "🗑️ Your chat history, memories, and conversation data have been cleared. Starting fresh! 🌱"
            await telegram_service.send_message(chat_id, response)
            
    except Exception as e:
        logger.error(f"Error handling /clear command: {e}")
        await telegram_service.send_message(update.effective_chat.id, "Sorry, there was an error clearing your data. Please try again later.")