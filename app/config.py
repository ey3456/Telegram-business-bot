import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    API_ID = int(os.getenv('API_ID', 0))
    API_HASH = os.getenv('API_HASH')
    BUSINESS_USER_ID = int(os.getenv('BUSINESS_USER_ID', 0))
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 8443))
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/business_bot.db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    TTS_LANGUAGE = os.getenv('TTS_LANGUAGE', 'zh-cn')
    TTS_TLD = os.getenv('TTS_TLD', 'com')
    TTS_AUDIO_SPEED = float(os.getenv('TTS_AUDIO_SPEED', 1.0))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/bot.log')
