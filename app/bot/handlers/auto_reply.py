import logging
from aiogram import Bot, types
from app.models.database import AutoReply, get_session

logger = logging.getLogger(__name__)


class AutoReplyHandler:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def add_reply(self, message: types.Message):
        raw = (message.text or "").replace("/addreply", "", 1).strip()
        if "|" not in raw:
            await message.answer("❌ 格式: /addreply 关键词 | 回复内容")
            return
        keyword, reply = raw.split("|", 1)
        keyword = keyword.strip()
        reply = reply.strip()
        if not keyword or not reply:
            await message.answer("❌ 关键词和回复都不能为空")
            return
        session = get_session()
        try:
            session.add(AutoReply(keyword=keyword, reply=reply, enabled=True))
            session.commit()
            await message.answer(f"✅ 自动回复已添加\n关键词: {keyword}")
        except Exception as exc:
            logger.error("添加自动回复失败: %s", exc)
            session.rollback()
            await message.answer("❌ 添加失败")
        finally:
            session.close()

    async def list_replies(self, message: types.Message):
        session = get_session()
        try:
            rules = session.query(AutoReply).filter_by(enabled=True).all()
            if not rules:
                await message.answer("📋 暂无自动回复规则")
                return
            lines = ["📋 自动回复列表：\n"]
            for rule in rules:
                lines.append(f"• {rule.keyword}\n  → {rule.reply}\n")
            await message.answer("\n".join(lines)[:4000])
        finally:
            session.close()

    async def maybe_reply(self, message: types.Message) -> bool:
        text = (message.text or "").strip()
        if not text:
            return False
        session = get_session()
        try:
            rules = session.query(AutoReply).filter_by(enabled=True).all()
            lowered = text.lower()
            for rule in rules:
                if rule.keyword.lower() in lowered:
                    await message.answer(rule.reply)
                    return True
            return False
        finally:
            session.close()
