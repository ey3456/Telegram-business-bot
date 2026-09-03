import logging
from aiogram import Bot, types

logger = logging.getLogger(__name__)

PRICING_TEXT = """💎 <b>订阅服务价格</b>

【基础版】免费
• 基础记账、TTS
• 最多 3 条自动回复

【专业版】¥29/月
• 无限记账
• 无限自动回复
• 最多 5 个搬运配置

【企业版】¥99/月
• 全部专业版功能
• 无限搬运
• 群发与 Business 防撤回
• 管理后台

使用 /subscribe 联系开通。
"""


class SubscriptionHandler:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def pricing(self, message: types.Message):
        await message.answer(PRICING_TEXT, parse_mode="HTML")

    async def subscribe(self, message: types.Message):
        await message.answer(
            "💎 订阅服务\n\n请联系管理员完成开通，支付后发送订单号即可启用套餐。"
        )
