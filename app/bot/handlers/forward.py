import logging
from aiogram import Bot, types
from app.models.database import ForwardConfig, get_session
from app.services.auth import is_admin

logger = logging.getLogger(__name__)


class ForwardHandler:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def add_forward(self, message: types.Message):
        if not is_admin(message.from_user.id):
            await message.answer("❌ 仅管理员可用此功能")
            return
        parts = (message.text or "").split()
        if len(parts) < 3:
            await message.answer("❌ 格式: /addforward &lt;源ID&gt; &lt;目标ID&gt;", parse_mode="HTML")
            return
        try:
            source_id = int(parts[1])
            target_id = int(parts[2])
        except ValueError:
            await message.answer("❌ ID 格式错误")
            return
        session = get_session()
        try:
            session.add(ForwardConfig(
                source_chat_id=source_id,
                target_chat_ids=[target_id],
                keywords=[],
                enabled=True,
            ))
            session.commit()
            await message.answer(f"✅ 搬运配置已添加\n源: {source_id}\n目标: {target_id}")
        except Exception as exc:
            logger.error("添加搬运失败: %s", exc)
            session.rollback()
            await message.answer("❌ 添加失败")
        finally:
            session.close()

    async def list_forward(self, message: types.Message):
        session = get_session()
        try:
            configs = session.query(ForwardConfig).filter_by(enabled=True).all()
            if not configs:
                await message.answer("📋 暂无搬运配置")
                return
            lines = ["📋 搬运配置列表：\n"]
            for cfg in configs:
                targets = ", ".join(str(t) for t in (cfg.target_chat_ids or []))
                lines.append(f"源: {cfg.source_chat_id}\n目标: {targets}\n")
            await message.answer("\n".join(lines))
        finally:
            session.close()

    async def maybe_forward(self, message: types.Message) -> bool:
        if message.chat.type not in {"group", "supergroup", "channel"}:
            return False
        session = get_session()
        try:
            configs = session.query(ForwardConfig).filter_by(
                source_chat_id=message.chat.id,
                enabled=True,
            ).all()
            forwarded = False
            for cfg in configs:
                keywords = cfg.keywords or []
                if keywords:
                    text = message.text or message.caption or ""
                    if not any(kw in text for kw in keywords):
                        continue
                for target_id in cfg.target_chat_ids or []:
                    try:
                        await self.bot.forward_message(
                            chat_id=target_id,
                            from_chat_id=message.chat.id,
                            message_id=message.message_id,
                        )
                        forwarded = True
                    except Exception as exc:
                        logger.error("转发失败 %s -> %s: %s", message.chat.id, target_id, exc)
            return forwarded
        finally:
            session.close()
