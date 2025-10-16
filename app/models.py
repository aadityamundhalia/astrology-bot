from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Time, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)  # Changed from Integer to BigInteger
    is_bot = Column(Boolean, default=False)
    first_name = Column(String)
    username = Column(String)
    language_code = Column(String)
    is_premium = Column(Boolean, default=False)
    date = Column(BigInteger)  # Also changed to BigInteger for timestamp
    date_of_birth = Column(String)
    time_of_birth = Column(String)
    place_of_birth = Column(String)
    horoscope_data = Column(JSON)
    horary_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    message_type = Column(String)  # 'user' or 'bot'
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
