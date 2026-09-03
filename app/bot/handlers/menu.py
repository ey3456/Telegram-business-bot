import logging
from aiogram import Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

HELP_TEXT = """📖 <b>统一机器人帮助</b>

<b>记账</b>
/expense — 记账菜单
/addexpense 类别 金额 描述
/expenses — 最近记录
/stats — 统计

<b>语音</b>
/tts 文本 — 文字转语音

<b>搬运（管理员）</b>
/addforward 源ID 目标ID
/listforward

<b>自动回复</b>
/addreply 关键词 | 回复内容
/listreply

<b>群发（管理员）</b>
/broadcast 消息内容

<b>订阅</b>
/pricing
/subscribe

<b>企业会话</b>
Business 消息会自动记录；编辑/删除会被防撤回模块保留。
"""


class MenuHandler:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def start(self, message: types.Message):
        await message.answer(
            "🤖 <b>统一 Telegram 机器人已启动</b>\n\n"
            "已合并：企业会话 / 防撤回 / 记账 / TTS / 搬运 / 自动回复 / 群发 / 订阅。\n"
            "使用 /menu 打开功能菜单，/help 查看命令。",
            parse_mode="HTML",
        )

    async def help(self, message: types.Message):
        await message.answer(HELP_TEXT, parse_mode="HTML")

    async def menu(self, message: types.Message):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 记账", callback_data="menu_expense")],
            [InlineKeyboardButton(text="🔊 TTS", callback_data="menu_tts")],
            [InlineKeyboardButton(text="🔄 搬运", callback_data="menu_forward")],
            [InlineKeyboardButton(text="🤖 自动回复", callback_data="menu_reply")],
            [InlineKeyboardButton(text="📢 群发", callback_data="menu_broadcast")],
            [InlineKeyboardButton(text="💎 订阅", callback_data="menu_subscribe")],
            [InlineKeyboardButton(text="❓ 帮助", callback_data="menu_help")],
        ])
        await message.answer("请选择功能：", reply_markup=keyboard)

    async def handle_callback(self, callback: types.CallbackQuery):
        data = callback.data
        texts = {
            "menu_expense": "💰 记账：/expense 或发送「午餐 35」\n/addexpense 餐饮 50 午餐\n/expenses /stats",
            "menu_tts": "🔊 语音：/tts 你好世界",
            "menu_forward": "🔄 搬运：/addforward 源ID 目标ID\n/listforward",
            "menu_reply": "🤖 自动回复：/addreply 你好 | 您好！\n/listreply",
            "menu_broadcast": "📢 群发：/broadcast 内容（仅管理员）",
            "menu_subscribe": None,
            "menu_help": HELP_TEXT,
        }
        if data == "menu_subscribe":
            await callback.message.edit_text(
                "💎 订阅：/pricing 查看套餐，/subscribe 联系开通。",
                parse_mode="HTML",
            )
            await callback.answer()
            return
        text = texts.get(data)
        if text:
            await callback.message.edit_text(text, parse_mode="HTML")
        await callback.answer()
