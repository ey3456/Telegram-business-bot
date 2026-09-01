#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
import threading
from flask import Flask, request
from app.config import Config
from app.bot.dispatcher import BotDispatcher
from app.models.database import init_db
from app.web.admin import app as flask_app
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE) if Config.LOG_FILE else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
def main():
    os.makedirs('./data', exist_ok=True)
    os.makedirs('./logs', exist_ok=True)
    os.makedirs('./data/tts_audio', exist_ok=True)
    init_db()
    bot_dispatcher = BotDispatcher()
    if Config.WEBHOOK_URL:
        logger.info(f"启动 Webhook 模式: {Config.WEBHOOK_URL}")
        asyncio.run(bot_dispatcher.setup_webhook())
        @flask_app.route('/webhook', methods=['POST'])
        async def webhook():
            from aiogram.types import Update
            update_data = request.get_json()
            await bot_dispatcher.handle_webhook(update_data)
            return 'OK'
        flask_app.run(host='0.0.0.0', port=Config.WEBHOOK_PORT, debug=False)
    else:
        logger.info("启动 Polling 模式...")
        def run_flask():
            flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        threading.Thread(target=run_flask, daemon=True).start()
        asyncio.run(bot_dispatcher.start_polling())
if __name__ == '__main__':
    main()
