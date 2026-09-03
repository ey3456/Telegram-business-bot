import logging
import hashlib
import os
from aiogram import Bot, types
from aiogram.types import FSInputFile
from gtts import gTTS
from app.models.database import get_session, TTSCache

logger = logging.getLogger(__name__)


class TTSHandler:
    AUDIO_DIR = './data/tts_audio/'
    MAX_TEXT_LENGTH = 2000

    def __init__(self, bot: Bot):
        self.bot = bot
        os.makedirs(self.AUDIO_DIR, exist_ok=True)

    async def handle_command(self, message: types.Message):
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("🔊 文字转语音\n用法: /tts 要转换的文本")
            return
        await self.speak_text(message, parts[1].strip())

    async def handle(self, message: types.Message):
        if not message.text or message.text.startswith('/'):
            return
        await self.speak_text(message, message.text.strip())

    async def speak_text(self, message: types.Message, text: str):
        if len(text) > self.MAX_TEXT_LENGTH:
            await message.answer(f"⚠️ 文本过长（{len(text)} 字符），限制 {self.MAX_TEXT_LENGTH}")
            return
        processing = await message.answer("🔄 生成语音...")
        try:
            audio_path = await self._get_or_generate_tts(text)
            if audio_path:
                audio_file = FSInputFile(audio_path)
                suffix = "..." if len(text) > 100 else ""
                await message.answer_voice(audio_file, caption=f"🔊 {text[:100]}{suffix}")
                await processing.delete()
            else:
                await processing.edit_text("❌ 生成失败")
        except Exception as exc:
            logger.error("TTS 错误: %s", exc)
            await processing.edit_text(f"❌ 错误: {exc}")

    async def _get_or_generate_tts(self, text: str) -> str:
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        audio_path = os.path.join(self.AUDIO_DIR, f"{text_hash}.mp3")
        if os.path.exists(audio_path):
            return audio_path
        try:
            tts = gTTS(text=text, lang='zh-cn', slow=False)
            tts.save(audio_path)
            session = get_session()
            try:
                cache = TTSCache(text_hash=text_hash, text=text[:500], audio_path=audio_path, language='zh-cn')
                session.add(cache)
                session.commit()
            finally:
                session.close()
            return audio_path
        except Exception as exc:
            logger.error("gTTS 失败: %s", exc)
            return None
