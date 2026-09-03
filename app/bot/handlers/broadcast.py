import logging
from aiogram import Bot, types
from app.models.database import User, get_session
from app.services.auth import is_admin

logger = logging.getLogger(__name__)


class BroadcastHandler:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def broadcast(self, message: types.Message):
        if not is_admin(message.from_user.id):
            await message.answer("❌ 仅管理员可用此功能")
            return
        content = (message.text or "").split(maxsplit=1)
        if len(content) < 2:
            await message.answer("❌ 请输入要群发的消息")
            return
        text = content[1]
        session = get_session()
        try:
            users = session.query(User).filter_by(is_active=True).all()
            sent = 0
            failed = 0
            for user in users:
                try:
                    await self.bot.send_message(user.telegram_id, text)
                    sent += 1
                except Exception as exc:
                    failed += 1
                    logger.warning("群发失败 %s: %s", user.telegram_id, exc)
            await message.answer(f"📢 群发完成：成功 {sent}，失败 {failed}")
        finally:
            session.close()
