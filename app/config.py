import os
from dotenv import load_dotenv

load_dotenv()


def _env_int(name: str, default: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    API_ID = _env_int('API_ID', 0)
    API_HASH = os.getenv('API_HASH')
    BUSINESS_USER_ID = _env_int('BUSINESS_USER_ID', 0)
    ADMIN_ID = _env_int('ADMIN_ID', _env_int('BUSINESS_USER_ID', 0))
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    WEBHOOK_PORT = _env_int('WEBHOOK_PORT', 8443)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/business_bot.db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    TTS_LANGUAGE = os.getenv('TTS_LANGUAGE', 'zh-cn')
    TTS_TLD = os.getenv('TTS_TLD', 'com')
    TTS_AUDIO_SPEED = _env_float('TTS_AUDIO_SPEED', 1.0)
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/bot.log')
