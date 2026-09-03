import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
Base = declarative_base()
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(50))
    is_business_owner = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = relationship("Message", back_populates="user")
    expenses = relationship("Expense", back_populates="user")
class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)
    business_connection_id = Column(String(255))
    chat_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    sender_type = Column(String(50))
    content_type = Column(String(50))
    content = Column(Text)
    file_id = Column(String(255))
    file_path = Column(String(512))
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    original_content = Column(Text)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="messages")
class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(100))
    description = Column(Text)
    expense_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_id = Column(Integer)
    user = relationship("User", back_populates="expenses")
class TTSCache(Base):
    __tablename__ = 'tts_cache'
    id = Column(Integer, primary_key=True)
    text_hash = Column(String(64), unique=True, index=True)
    text = Column(Text)
    audio_path = Column(String(512))
    language = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)
class SystemLog(Base):
    __tablename__ = 'system_logs'
    id = Column(Integer, primary_key=True)
    level = Column(String(20))
    module = Column(String(100))
    message = Column(Text)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class ForwardConfig(Base):
    __tablename__ = 'forward_config'
    id = Column(Integer, primary_key=True)
    source_chat_id = Column(Integer, nullable=False, index=True)
    target_chat_ids = Column(JSON, nullable=False)
    keywords = Column(JSON)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AutoReply(Base):
    __tablename__ = 'auto_replies'
    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), nullable=False, index=True)
    reply = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, index=True)
    plan = Column(String(50), nullable=False)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User")
def get_engine():
    db_url = os.getenv('DATABASE_URL', 'sqlite:///./data/business_bot.db')
    if db_url.startswith('sqlite:///'):
        os.makedirs(os.path.dirname(db_url.replace('sqlite:///', '')), exist_ok=True)
    return create_engine(db_url, echo=False)
def init_db():
    Base.metadata.create_all(get_engine())
def get_session():
    Session = sessionmaker(bind=get_engine())
    return Session()
