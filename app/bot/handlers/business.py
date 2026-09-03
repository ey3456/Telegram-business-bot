import logging
from datetime import datetime
from aiogram import Bot, types
from aiogram.types import BusinessConnection
from app.models.database import get_session, User, Message as DBMessage
logger = logging.getLogger(__name__)
class BusinessHandler:
    def __init__(self, bot: Bot):
        self.bot = bot
    async def handle_connection(self, connection: BusinessConnection):
        session = get_session()
        try:
            user = connection.user
            db_user = session.query(User).filter_by(telegram_id=user.id).first()
            if not db_user:
                db_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_business_owner=True
                )
                session.add(db_user)
                session.commit()
            logger.info(f"Business 连接: {user.id}")
        except Exception as e:
            logger.error(f"连接处理失败: {e}")
            session.rollback()
        finally:
            session.close()
    async def handle(self, message: types.Message):
        session = get_session()
        try:
            user_id = message.from_user.id
            db_user = session.query(User).filter_by(telegram_id=user_id).first()
            if not db_user:
                db_user = User(
                    telegram_id=user_id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name
                )
                session.add(db_user)
                session.commit()
            sender_type = 'customer'
            if user_id == self.bot.id:
                sender_type = 'bot'
            elif hasattr(message, 'business_connection_id') and message.business_connection_id:
                try:
                    conn = await self.bot.get_business_connection(message.business_connection_id)
                    if conn and conn.user.id == user_id:
                        sender_type = 'business_owner'
                except Exception:
                    pass
            content = ''
            content_type = 'text'
            file_id = None
            if message.text:
                content = message.text
            elif message.caption:
                content = message.caption
                content_type = 'caption'
            elif message.photo:
                content_type = 'photo'
                file_id = message.photo[-1].file_id
            elif message.document:
                content_type = 'document'
                file_id = message.document.file_id
                content = message.document.file_name or ''
            elif message.voice:
                content_type = 'voice'
                file_id = message.voice.file_id
            elif message.video:
                content_type = 'video'
                file_id = message.video.file_id
            elif message.audio:
                content_type = 'audio'
                file_id = message.audio.file_id
            db_msg = DBMessage(
                message_id=message.message_id,
                business_connection_id=getattr(message, 'business_connection_id', ''),
                chat_id=message.chat.id,
                user_id=db_user.id,
                sender_type=sender_type,
                content_type=content_type,
                content=content[:5000] if content else '',
                file_id=file_id,
                created_at=datetime.utcnow()
            )
            session.add(db_msg)
            session.commit()
            logger.info(f"消息保存: {message.message_id}")
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            session.rollback()
        finally:
            session.close()
