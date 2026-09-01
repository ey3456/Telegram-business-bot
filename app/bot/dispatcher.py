import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import BusinessConnection, BusinessMessagesDeleted
from app.config import Config
from app.bot.handlers.business import BusinessHandler
from app.bot.handlers.anti_revoke import AntiRevokeHandler
from app.bot.handlers.expense import ExpenseHandler
from app.bot.handlers.tts import TTSHandler
from app.bot.middlewares.db_middleware import DBMiddleware
logger = logging.getLogger(__name__)
class BotDispatcher:
    def __init__(self):
        self.bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dp = Dispatcher()
        self._setup_middlewares()
        self._setup_handlers()
    def _setup_middlewares(self):
        self.dp.message.middleware(DBMiddleware())
        self.dp.business_message.middleware(DBMiddleware())
    def _setup_handlers(self):
        self.business_handler = BusinessHandler(self.bot)
        self.anti_revoke_handler = AntiRevokeHandler(self.bot)
        self.expense_handler = ExpenseHandler(self.bot)
        self.tts_handler = TTSHandler(self.bot)
        @self.dp.business_message()
        async def handle_business_message(message: types.Message):
            await self.business_handler.handle(message)
        @self.dp.edited_business_message()
        async def handle_edited_business_message(message: types.Message):
            await self.anti_revoke_handler.handle_edit(message)
        @self.dp.business_messages_deleted()
        async def handle_business_messages_deleted(event: BusinessMessagesDeleted):
            await self.anti_revoke_handler.handle_delete(event)
        @self.dp.business_connection()
        async def handle_business_connection(connection: BusinessConnection):
            await self.business_handler.handle_connection(connection)
        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            await message.answer("🤖 企业版机器人已启动。\n请通过 Business 账号发送消息。")
        @self.dp.message(Command("expense"))
        async def cmd_expense(message: types.Message):
            await self.expense_handler.handle_command(message)
        @self.dp.message(Command("tts"))
        async def cmd_tts(message: types.Message):
            await self.tts_handler.handle_command(message)
        @self.dp.callback_query()
        async def handle_callback(callback: types.CallbackQuery):
            if callback.data.startswith('expense_'):
                await self.expense_handler.handle_callback(callback)
    async def start_polling(self):
        logger.info("启动轮询...")
        await self.dp.start_polling(self.bot)
    async def setup_webhook(self):
        webhook_url = f"{Config.WEBHOOK_URL}/webhook"
        await self.bot.set_webhook(url=webhook_url, allowed_updates=self.dp.resolve_used_update_types())
        logger.info(f"Webhook 设置: {webhook_url}")
    async def handle_webhook(self, update: dict):
        telegram_update = types.Update(**update)
        await self.dp.feed_update(self.bot, telegram_update)
