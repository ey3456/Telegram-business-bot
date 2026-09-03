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
from app.bot.handlers.menu import MenuHandler
from app.bot.handlers.forward import ForwardHandler
from app.bot.handlers.auto_reply import AutoReplyHandler
from app.bot.handlers.broadcast import BroadcastHandler
from app.bot.handlers.subscription import SubscriptionHandler
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
        self.menu_handler = MenuHandler(self.bot)
        self.forward_handler = ForwardHandler(self.bot)
        self.auto_reply_handler = AutoReplyHandler(self.bot)
        self.broadcast_handler = BroadcastHandler(self.bot)
        self.subscription_handler = SubscriptionHandler(self.bot)

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
            await self.menu_handler.start(message)

        @self.dp.message(Command("help"))
        async def cmd_help(message: types.Message):
            await self.menu_handler.help(message)

        @self.dp.message(Command("menu"))
        async def cmd_menu(message: types.Message):
            await self.menu_handler.menu(message)

        @self.dp.message(Command("expense"))
        async def cmd_expense(message: types.Message):
            await self.expense_handler.handle_command(message)

        @self.dp.message(Command("addexpense"))
        async def cmd_add_expense(message: types.Message):
            await self.expense_handler.add_expense_command(message)

        @self.dp.message(Command("expenses"))
        async def cmd_expenses(message: types.Message):
            await self.expense_handler.view_expenses(message)

        @self.dp.message(Command("stats"))
        async def cmd_stats(message: types.Message):
            await self.expense_handler.stats(message)

        @self.dp.message(Command("tts"))
        async def cmd_tts(message: types.Message):
            await self.tts_handler.handle_command(message)

        @self.dp.message(Command("addforward"))
        async def cmd_add_forward(message: types.Message):
            await self.forward_handler.add_forward(message)

        @self.dp.message(Command("listforward"))
        async def cmd_list_forward(message: types.Message):
            await self.forward_handler.list_forward(message)

        @self.dp.message(Command("addreply"))
        async def cmd_add_reply(message: types.Message):
            await self.auto_reply_handler.add_reply(message)

        @self.dp.message(Command("listreply"))
        async def cmd_list_reply(message: types.Message):
            await self.auto_reply_handler.list_replies(message)

        @self.dp.message(Command("broadcast"))
        async def cmd_broadcast(message: types.Message):
            await self.broadcast_handler.broadcast(message)

        @self.dp.message(Command("pricing"))
        async def cmd_pricing(message: types.Message):
            await self.subscription_handler.pricing(message)

        @self.dp.message(Command("subscribe"))
        async def cmd_subscribe(message: types.Message):
            await self.subscription_handler.subscribe(message)

        @self.dp.message()
        async def handle_plain_message(message: types.Message):
            if await self.auto_reply_handler.maybe_reply(message):
                return
            if await self.forward_handler.maybe_forward(message):
                return
            if message.text:
                await self.expense_handler.handle(message)

        @self.dp.callback_query()
        async def handle_callback(callback: types.CallbackQuery):
            data = callback.data or ""
            if data.startswith("expense_"):
                await self.expense_handler.handle_callback(callback)
                return
            if data.startswith("menu_"):
                await self.menu_handler.handle_callback(callback)
                return
            await callback.answer()

    async def start_polling(self):
        logger.info("启动轮询...")
        await self.dp.start_polling(self.bot)

    async def setup_webhook(self):
        webhook_url = f"{Config.WEBHOOK_URL}/webhook"
        await self.bot.set_webhook(url=webhook_url, allowed_updates=self.dp.resolve_used_update_types())
        logger.info("Webhook 设置: %s", webhook_url)

    async def handle_webhook(self, update: dict):
        telegram_update = types.Update(**update)
        await self.dp.feed_update(self.bot, telegram_update)
