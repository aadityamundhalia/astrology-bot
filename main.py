import logging
from fastapi import FastAPI, Depends
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import re
from datetime import datetime

from config import get_settings
from app.database import get_db, engine
from app.models import Base, User
from app.services.telegram_service import TelegramService
from app.services.memory_service import MemoryService
from app.services.astrology_service import AstrologyService
from app.agents.extraction_agent import ExtractionAgent
from app.agents.rudie_agent import RudieAgent
from app.database import AsyncSessionLocal

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

# Database initialization
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

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
    try:
        message = update.message
        user_id = message.from_user.id
        chat_id = message.chat.id
        text = message.text
        
        logger.info(f"Received message from user {user_id}: {text}")
        
        # Send typing indicator
        await telegram_service.send_typing(chat_id)
        
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
                    
                    response = "Thanks for sharing your details 🌿\nWhat would you like me to look into for you today? 🌞"
                    await telegram_service.send_message(chat_id, response)
                    return
                else:
                    # Ask for birth data
                    response = ("Please provide below in exact format:\n\n"
                               "Date of Birth: 1970-11-22\n"
                               "Time of Birth: 00:25\n"
                               "Place of Birth: Hisar, Haryana")
                    await telegram_service.send_message(chat_id, response)
                    return
            
            # User has birth data, process astrology query
            await telegram_service.send_typing(chat_id)
            
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
            
            # Generate response using Rudie agent
            response = await rudie_agent.generate_response(
                user_message=text,
                user_context=user_context,
                astrology_service=astrology_service
            )
            
            # Remove thinking tags if present
            response = re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL)
            response = response.strip()
            
            # Send response
            await telegram_service.send_message(chat_id, response)
            
            # Add to memory
            await memory_service.add_memory(user_id, text, response)
            
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        try:
            await telegram_service.send_message(
                chat_id,
                "Sorry, something went wrong. Please try again! 🌿"
            )
        except:
            pass

@app.on_event("startup")
async def start_bot():
    """Start telegram bot"""
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
