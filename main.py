import logging
# Suppress httpx INFO logs to reduce clutter
logging.getLogger("httpx").setLevel(logging.WARNING)

from fastapi import FastAPI, Depends
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    CommandHandler,
    ConversationHandler
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import re
from datetime import datetime
import asyncio
import httpx

from config import get_settings
from app.database import get_db, engine, AsyncSessionLocal
from app.models import Base, User
from app.services.telegram_service import TelegramService
from app.services.memory_service import MemoryService
from app.services.astrology_service import AstrologyService
from app.agents.extraction_agent import ExtractionAgent
from app.agents.rudie_agent import RudieAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="Rudie Astrology Bot")

# Initialize services
telegram_service = TelegramService()
memory_service = MemoryService()
astrology_service = AstrologyService()
extraction_agent = ExtractionAgent()
rudie_agent = RudieAgent()

def validate_birth_data(date_str: str, time_str: str, place_str: str) -> bool:
    """Validate birth data format"""
    if not all([date_str, time_str, place_str]):
        return False
    
    # Check date format (YYYY-MM-DD)
    if not re.match(r'\d{4}-\d{2}-\d{2}', str(date_str)):
        return False
    
    # Check time format (HH:MM)
    if not re.match(r'\d{2}:\d{2}', str(time_str)):
        return False
    
    # Check place format (has comma)
    if ',' not in str(place_str):
        return False
    
    return True

async def handle_clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command"""
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        logger.info(f"🗑️ Clear command received from user {user_id}")
        
        async with AsyncSessionLocal() as db:
            # Clear chat history
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
                        logger.info(f"🧠 Mem0 cleared: {message_count} messages and memories for user {user_id}")
                    else:
                        logger.warning(f"🧠 Mem0 clear failed: HTTP {response.status_code}")
                except Exception as e:
                    logger.error(f"🧠 Mem0 clear error: {e}")
            
            # Send confirmation
            response = "🗑️ Your chat history, memories, and conversation data have been cleared. Starting fresh! 🌱"
            await telegram_service.send_message(chat_id, response)
            
    except Exception as e:
        logger.error(f"Error handling /clear command: {e}")
        await telegram_service.send_message(update.effective_chat.id, "Sorry, there was an error clearing your data. Please try again later.")

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Check if user already has birth details
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
            # User already has details
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
            # New user - needs setup
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

async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setup command - alias for /change"""
    return await start_birth_details_wizard(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming telegram messages"""
    # Create stop event for typing indicator
    stop_typing = asyncio.Event()
    typing_task = None
    
    try:
        message = update.message
        user_id = message.from_user.id
        chat_id = message.chat.id
        text = message.text
        
        logger.info(f"📥 Telegram received: user {user_id} - {len(text)} chars: {text}")
        
        # Start continuous typing indicator
        typing_task = asyncio.create_task(
            telegram_service.keep_typing(chat_id, stop_typing)
        )
        
        # Get database session
        async with AsyncSessionLocal() as db:
            # Upsert user
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    id=user_id,
                    is_bot=message.from_user.is_bot,
                    first_name=message.from_user.first_name,
                    username=message.from_user.username,
                    language_code=message.from_user.language_code,
                    is_premium=message.from_user.is_premium or False,
                    date=int(message.date.timestamp())
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            
            # Check if user has complete birth data
            has_birth_data = validate_birth_data(
                user.date_of_birth, 
                user.time_of_birth, 
                user.place_of_birth
            )
            
            # Try to extract birth data from message (for new users OR updates)
            extracted = await extraction_agent.extract_birth_data(text)
            
            if extracted and all([
                extracted.get("date_of_birth"),
                extracted.get("time_of_birth"),
                extracted.get("place_of_birth")
            ]):
                # Check if this is an update (user already has data)
                is_update = has_birth_data
                
                # Store old details for logging
                old_details = None
                if is_update:
                    old_details = {
                        "date": user.date_of_birth,
                        "time": user.time_of_birth,
                        "place": user.place_of_birth
                    }
                
                # Update user with birth data
                user.date_of_birth = extracted["date_of_birth"]
                user.time_of_birth = extracted["time_of_birth"]
                user.place_of_birth = extracted["place_of_birth"]
                await db.commit()
                
                # Stop typing and send response
                stop_typing.set()
                if typing_task:
                    await typing_task
                
                if is_update:
                    logger.info(f"🔄 User {user_id} updated birth details")
                    logger.info(f"   Old: {old_details}")
                    logger.info(f"   New: DOB={extracted['date_of_birth']}, TOB={extracted['time_of_birth']}, POB={extracted['place_of_birth']}")
                    
                    response = f"""✅ **Birth Details Updated!**

📅 Date of Birth: {extracted['date_of_birth']}
🕐 Time of Birth: {extracted['time_of_birth']}
📍 Place of Birth: {extracted['place_of_birth']}

Your cosmic profile has been refreshed! What would you like to know? 🌟"""
                else:
                    response = "Thanks for sharing your details 🌿\nWhat would you like me to look into for you today? 🌞"
                
                await telegram_service.send_message(chat_id, response)
                return
            
            # If no birth data in message and user doesn't have data, ask for it
            if not has_birth_data:
                # Stop typing and ask for birth data
                stop_typing.set()
                if typing_task:
                    await typing_task
                
                response = ("Please provide your birth details in this exact format:\n\n"
                           "Date of Birth: 1970-11-22\n"
                           "Time of Birth: 00:25\n"
                           "Place of Birth: Hisar, Haryana")
                await telegram_service.send_message(chat_id, response)
                return
            
            # User has birth data, process astrology query
            # (typing indicator is still running)
            
            # Get memories (with safe fallback)
            try:
                memories_result = await memory_service.get_memories(user_id, text)
                memory_data = ""
                
                if memories_result and isinstance(memories_result, dict):
                    memory_data = memories_result.get("data", "")
                else:
                    logger.warning(f"🧠 Invalid memories result: {type(memories_result)}")
                    memory_data = ""
                    
            except Exception as e:
                logger.warning(f"🧠 Failed to get memories, continuing without: {e}")
                memory_data = ""

            # Prepare user context
            user_context = {
                "name": user.first_name,
                "date_of_birth": user.date_of_birth,
                "time_of_birth": user.time_of_birth,
                "place_of_birth": user.place_of_birth,
                "memories": memory_data
            }
            
            # Generate response using Rudie agent (typing continues during this)
            response = await rudie_agent.generate_response(
                user_message=text,
                user_context=user_context,
                astrology_service=astrology_service
            )
            
            # Remove thinking tags if present
            response = re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL)
            response = response.strip()
            
            # Stop typing indicator
            stop_typing.set()
            if typing_task:
                await typing_task
            
            # Send response
            await telegram_service.send_message(chat_id, response)
            
            # Save to database and Redis
            await telegram_service.save_chat_to_db(db, user_id, "user", text)
            await telegram_service.save_chat_to_db(db, user_id, "bot", response)
            telegram_service.save_chat_to_redis(user_id, "user", text)
            telegram_service.save_chat_to_redis(user_id, "bot", response)
            
            # Add to memory (in background, don't wait)
            async def add_memory_safe():
                try:
                    await memory_service.add_memory(user_id, text, response)
                except Exception as e:
                    logger.error(f"Failed to add memory in background: {e}")

            asyncio.create_task(add_memory_safe())

            
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        
        # Stop typing on error
        stop_typing.set()
        if typing_task:
            try:
                await typing_task
            except:
                pass
        
        try:
            await telegram_service.send_message(
                chat_id,
                "Sorry, something went wrong. Please try again! 🌿"
            )
        except:
            pass
    finally:
        # Ensure typing is stopped
        stop_typing.set()
        if typing_task and not typing_task.done():
            try:
                await typing_task
            except:
                pass

async def handle_change_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /change command to update birth details"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    logger.info(f"🔄 Change command received from user {user_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user and validate_birth_data(user.date_of_birth, user.time_of_birth, user.place_of_birth):
                # Show current details
                current_details = f"""📝 **Your Current Birth Details:**

📅 Date of Birth: {user.date_of_birth}
🕐 Time of Birth: {user.time_of_birth}
📍 Place of Birth: {user.place_of_birth}

To update your details, please send them in this format:

Date of Birth: 1990-01-15
Time of Birth: 10:30
Place of Birth: New Delhi, India

I'll update your profile once you send the new details! 🌟"""
            else:
                current_details = """You haven't set your birth details yet.

Please send them in this format:

Date of Birth: 1990-01-15
Time of Birth: 10:30
Place of Birth: New Delhi, India"""
            
            await telegram_service.send_message(chat_id, current_details)
            
    except Exception as e:
        logger.error(f"Error handling /change command: {e}")
        await telegram_service.send_message(chat_id, "Sorry, there was an error. Please try again!")

# Conversation states
BIRTH_DATE, BIRTH_TIME, BIRTH_PLACE = range(3)

async def start_birth_details_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the birth details collection wizard"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Check if updating or setting for first time
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        context.user_data['is_update'] = user and validate_birth_data(
            user.date_of_birth, user.time_of_birth, user.place_of_birth
        )
    
    if context.user_data.get('is_update'):
        message = "✨ Let's update your birth details!\n\n📅 **Step 1 of 3**\n\nWhat's your date of birth?\n\nPlease enter in format: YYYY-MM-DD\nExample: 1990-01-15"
    else:
        message = "Welcome! 🌿 Let me gather your birth details so I can give you personalized cosmic guidance.\n\n📅 **Step 1 of 3**\n\nWhat's your date of birth?\n\nPlease enter in format: YYYY-MM-DD\nExample: 1990-01-15"
    
    await telegram_service.send_message(chat_id, message)
    return BIRTH_DATE

async def receive_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate birth date"""
    chat_id = update.effective_chat.id
    date_text = update.message.text.strip()
    
    # Validate format
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_text):
        await telegram_service.send_message(
            chat_id,
            "❌ Invalid format! Please use YYYY-MM-DD\n\nExample: 1990-01-15"
        )
        return BIRTH_DATE
    
    # Validate actual date
    try:
        from datetime import datetime
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        await telegram_service.send_message(
            chat_id,
            "❌ That doesn't look like a valid date. Please check and try again.\n\nExample: 1990-01-15"
        )
        return BIRTH_DATE
    
    # Store and move to next step
    context.user_data['birth_date'] = date_text
    
    await telegram_service.send_message(
        chat_id,
        f"✅ Got it! {date_text}\n\n🕐 **Step 2 of 3**\n\nWhat time were you born?\n\nPlease enter in 24-hour format: HH:MM\nExample: 14:30 (for 2:30 PM)\nExample: 09:15 (for 9:15 AM)"
    )
    return BIRTH_TIME

async def receive_birth_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate birth time"""
    chat_id = update.effective_chat.id
    time_text = update.message.text.strip()
    
    # Validate format
    if not re.match(r'^\d{2}:\d{2}$', time_text):
        await telegram_service.send_message(
            chat_id,
            "❌ Invalid format! Please use HH:MM (24-hour format)\n\nExample: 14:30 or 09:15"
        )
        return BIRTH_TIME
    
    # Validate actual time
    try:
        hour, minute = map(int, time_text.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        await telegram_service.send_message(
            chat_id,
            "❌ That doesn't look like a valid time. Please check and try again.\n\nExample: 14:30 or 09:15"
        )
        return BIRTH_TIME
    
    # Store and move to next step
    context.user_data['birth_time'] = time_text
    
    await telegram_service.send_message(
        chat_id,
        f"✅ Perfect! {time_text}\n\n📍 **Step 3 of 3**\n\nWhere were you born?\n\nPlease enter: City, Region/State\nExample: New Delhi, India\nExample: Sydney, New South Wales"
    )
    return BIRTH_PLACE

async def receive_birth_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive birth place and save all details"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    place_text = update.message.text.strip()
    
    # Validate format (must have comma)
    if ',' not in place_text:
        await telegram_service.send_message(
            chat_id,
            "❌ Please include both city and region/state separated by a comma.\n\nExample: Mumbai, Maharashtra\nExample: London, England"
        )
        return BIRTH_PLACE
    
    # Store place
    context.user_data['birth_place'] = place_text
    
    # Save to database
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                id=user_id,
                is_bot=update.effective_user.is_bot,
                first_name=update.effective_user.first_name,
                username=update.effective_user.username,
                language_code=update.effective_user.language_code,
                is_premium=update.effective_user.is_premium or False,
                date=int(update.message.date.timestamp())
            )
            db.add(user)
        
        user.date_of_birth = context.user_data['birth_date']
        user.time_of_birth = context.user_data['birth_time']
        user.place_of_birth = context.user_data['birth_place']
        
        await db.commit()
    
    # Send confirmation
    is_update = context.user_data.get('is_update', False)
    
    if is_update:
        confirmation = f"""✅ **Birth Details Updated!**

📅 Date of Birth: {context.user_data['birth_date']}
🕐 Time of Birth: {context.user_data['birth_time']}
📍 Place of Birth: {context.user_data['birth_place']}

Your cosmic profile has been refreshed! What would you like to know? 🌟"""
    else:
        confirmation = f"""🎉 **All Set!**

📅 Date of Birth: {context.user_data['birth_date']}
🕐 Time of Birth: {context.user_data['birth_time']}
📍 Place of Birth: {context.user_data['birth_place']}

Thanks for sharing your details! I'm ready to give you personalized cosmic guidance. What would you like to know? 🌿✨"""
    
    await telegram_service.send_message(chat_id, confirmation)
    
    logger.info(f"{'🔄 Updated' if is_update else '✅ Set'} birth details for user {user_id}")
    
    # Clear conversation data
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation"""
    await telegram_service.send_message(
        update.effective_chat.id,
        "Cancelled! You can start again anytime with /change or /start 🌿",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

# Create conversation handler for birth details wizard
birth_details_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("change", start_birth_details_wizard),
        CommandHandler("setup", start_birth_details_wizard),  # This line
    ],
    states={
        BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_birth_date)],
        BIRTH_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_birth_time)],
        BIRTH_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_birth_place)],
    },
    fallbacks=[CommandHandler("cancel", cancel_wizard)],
    name="birth_details",
    persistent=False,
)


@app.on_event("startup")
async def start_bot():
    """Start telegram bot"""
    logger.info("🚀 Starting astrology bot...")
    
    # Test Mem0 connection
    try:
        logger.info("🧠 Testing Mem0 connection...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.mem0_service_url}/")
            logger.info(f"🧠 Mem0 service responding: HTTP {response.status_code}")
    except Exception as e:
        logger.warning(f"🧠 Could not connect to Mem0 service: {e}")
        logger.warning("⚠️  Bot will continue but memory features may not work")
    
    # Start Telegram bot
    application = telegram_service.setup_application(
        message_handler=handle_message,
        conversation_handler=birth_details_conversation,
        clear_handler=handle_clear_command,
        start_handler=handle_start_command,
        help_handler=handle_help_command,
        info_handler=handle_info_command
    )
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("✅ Telegram bot started successfully")

@app.on_event("shutdown")
async def stop_bot():
    """Stop telegram bot"""
    if telegram_service.application:
        await telegram_service.application.updater.stop()
        await telegram_service.application.stop()
        await telegram_service.application.shutdown()
    logger.info("Telegram bot stopped")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8282, reload=True)
