import logging
from datetime import datetime
from aiogram import Bot, types
from aiogram.types import BusinessMessagesDeleted
from app.models.database import get_session, Message as DBMessage
logger = logging.getLogger(__name__)
class AntiRevokeHandler:
    def __init__(self, bot: Bot):
        self.bot = bot
    async def handle_edit(self, message: types.Message):
        session = get_session()
        try:
            db_msg = session.query(DBMessage).filter_by(
                message_id=message.message_id,
                chat_id=message.chat.id
            ).first()
            if db_msg:
                if not db_msg.original_content:
                    db_msg.original_content = db_msg.content
                else:
                    db_msg.original_content += f"\n---[EDIT:{datetime.utcnow()}]---\n{db_msg.content}"
                db_msg.content = message.text or message.caption or ''
                db_msg.is_edited = True
                db_msg.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"编辑记录: {message.message_id}")
        except Exception as e:
            logger.error(f"编辑处理失败: {e}")
            session.rollback()
        finally:
            session.close()
    async def handle_delete(self, event: BusinessMessagesDeleted):
        session = get_session()
        try:
            chat_id = event.chat.id
            for msg_id in event.message_ids:
                db_msg = session.query(DBMessage).filter_by(message_id=msg_id, chat_id=chat_id).first()
                if db_msg:
                    db_msg.is_deleted = True
                    db_msg.deleted_at = datetime.utcnow()
            session.commit()
            logger.info(f"删除标记: {len(event.message_ids)} 条")
        except Exception as e:
            logger.error(f"删除处理失败: {e}")
            session.rollback()
        finally:
            session.close()
