"""Conversation handlers for birth details wizard"""
import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from sqlalchemy import select
import re
from datetime import datetime

from app.database import AsyncSessionLocal
from app.models import User
from app.utils.validators import validate_birth_data

logger = logging.getLogger(__name__)

# Conversation states
BIRTH_DATE, BIRTH_TIME, BIRTH_PLACE = range(3)

async def start_birth_details_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_service) -> int:
    """Start the birth details collection wizard"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
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

async def receive_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_service) -> int:
    """Receive and validate birth date"""
    chat_id = update.effective_chat.id
    date_text = update.message.text.strip()
    
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_text):
        await telegram_service.send_message(
            chat_id,
            "❌ Invalid format! Please use YYYY-MM-DD\n\nExample: 1990-01-15"
        )
        return BIRTH_DATE
    
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        await telegram_service.send_message(
            chat_id,
            "❌ That doesn't look like a valid date. Please check and try again.\n\nExample: 1990-01-15"
        )
        return BIRTH_DATE
    
    context.user_data['birth_date'] = date_text
    
    await telegram_service.send_message(
        chat_id,
        f"✅ Got it! {date_text}\n\n🕐 **Step 2 of 3**\n\nWhat time were you born?\n\nPlease enter in 24-hour format: HH:MM\nExample: 14:30 (for 2:30 PM)\nExample: 09:15 (for 9:15 AM)"
    )
    return BIRTH_TIME

async def receive_birth_time(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_service) -> int:
    """Receive and validate birth time"""
    chat_id = update.effective_chat.id
    time_text = update.message.text.strip()
    
    if not re.match(r'^\d{2}:\d{2}$', time_text):
        await telegram_service.send_message(
            chat_id,
            "❌ Invalid format! Please use HH:MM (24-hour format)\n\nExample: 14:30 or 09:15"
        )
        return BIRTH_TIME
    
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
    
    context.user_data['birth_time'] = time_text
    
    await telegram_service.send_message(
        chat_id,
        f"✅ Perfect! {time_text}\n\n📍 **Step 3 of 3**\n\nWhere were you born?\n\nPlease enter: City, Region/State\nExample: New Delhi, India\nExample: Sydney, New South Wales"
    )
    return BIRTH_PLACE

async def receive_birth_place(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_service) -> int:
    """Receive birth place and save all details"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    place_text = update.message.text.strip()
    
    if ',' not in place_text:
        await telegram_service.send_message(
            chat_id,
            "❌ Please include both city and region/state separated by a comma.\n\nExample: Mumbai, Maharashtra\nExample: London, England"
        )
        return BIRTH_PLACE
    
    context.user_data['birth_place'] = place_text
    
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
    
    context.user_data.clear()
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

async def cancel_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_service) -> int:
    """Cancel the conversation"""
    await telegram_service.send_message(
        update.effective_chat.id,
        "Cancelled! You can start again anytime with /change or /start 🌿",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END