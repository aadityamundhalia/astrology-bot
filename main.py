import logging
# Suppress httpx INFO logs to reduce clutter
logging.getLogger("httpx").setLevel(logging.WARNING)

from fastapi import FastAPI, Depends
from telegram import Update
from telegram.ext import ContextTypes
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
        
        logger.info(f"Received message from user {user_id}: {text}")
        
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
            
            if not has_birth_data:
                # Try to extract birth data from message
                extracted = await extraction_agent.extract_birth_data(text)
                
                if extracted and all([
                    extracted.get("date_of_birth"),
                    extracted.get("time_of_birth"),
                    extracted.get("place_of_birth")
                ]):
                    # Update user with birth data
                    user.date_of_birth = extracted["date_of_birth"]
                    user.time_of_birth = extracted["time_of_birth"]
                    user.place_of_birth = extracted["place_of_birth"]
                    await db.commit()
                    
                    # Stop typing and send response
                    stop_typing.set()
                    if typing_task:
                        await typing_task
                    
                    response = "Thanks for sharing your details 🌿\nWhat would you like me to look into for you today? 🌞"
                    await telegram_service.send_message(chat_id, response)
                    return
                else:
                    # Stop typing and ask for birth data
                    stop_typing.set()
                    if typing_task:
                        await typing_task
                    
                    response = ("Please provide below in exact format:\n\n"
                               "Date of Birth: 1970-11-22\n"
                               "Time of Birth: 00:25\n"
                               "Place of Birth: Hisar, Haryana")
                    await telegram_service.send_message(chat_id, response)
                    return
            
            # User has birth data, process astrology query
            # (typing indicator is still running)
            
            # Get memories
            memories = await memory_service.get_memories(user_id, text)
            
            # Prepare user context
            user_context = {
                "name": user.first_name,
                "date_of_birth": user.date_of_birth,
                "time_of_birth": user.time_of_birth,
                "place_of_birth": user.place_of_birth,
                "memories": memories.get("data", "")
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

@app.on_event("startup")
async def start_bot():
    """Start telegram bot"""
    # Test Mem0 connection
    try:
        logger.info("Testing Mem0 connection...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.mem0_service_url}/")
            logger.info(f"Mem0 service status: {response.status_code}")
    except Exception as e:
        logger.warning(f"Could not connect to Mem0 service: {e}")
        logger.warning("Bot will continue but memory features may not work")
    
    application = telegram_service.setup_application(handle_message)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("Telegram bot started")

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
