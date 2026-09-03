import logging
import re
from datetime import datetime, timedelta
from aiogram import Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.models.database import get_session, User, Expense
from app.services.expense_service import ExpenseService
logger = logging.getLogger(__name__)
class ExpenseHandler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.service = ExpenseService()
    def _parse_command_args(self, message: types.Message):
        parts = (message.text or "").split(maxsplit=1)
        return parts[1].split() if len(parts) > 1 else []

    async def add_expense_command(self, message: types.Message):
        args = self._parse_command_args(message)
        if len(args) < 3:
            await message.answer("❌ 格式: /addexpense 类别 金额 描述")
            return
        category = args[0]
        try:
            amount = -abs(float(args[1].replace(",", "")))
        except ValueError:
            await message.answer("❌ 金额格式错误")
            return
        description = " ".join(args[2:])
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
            if not user:
                user = User(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                )
                session.add(user)
                session.commit()
            expense = Expense(
                user_id=user.id,
                amount=amount,
                category=category,
                description=description[:500],
                message_id=message.message_id,
            )
            session.add(expense)
            session.commit()
            await message.answer(
                f"✅ 记账成功\n类别: {category}\n金额: ¥{abs(amount):.2f}\n描述: {description}"
            )
        except Exception as exc:
            logger.error("命令记账失败: %s", exc)
            session.rollback()
            await message.answer("❌ 记账失败")
        finally:
            session.close()

    async def view_expenses(self, message: types.Message):
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
            if not user:
                await message.answer("📊 暂无支出记录")
                return
            rows = (
                session.query(Expense)
                .filter_by(user_id=user.id)
                .order_by(Expense.expense_date.desc())
                .limit(10)
                .all()
            )
            if not rows:
                await message.answer("📊 暂无支出记录")
                return
            lines = ["📊 最近支出记录：\n"]
            for exp in rows:
                kind = "收入" if exp.amount > 0 else "支出"
                lines.append(
                    f"• {exp.expense_date.strftime('%Y-%m-%d %H:%M')} | {exp.category} | "
                    f"{kind} ¥{abs(exp.amount):.2f}\n  {exp.description or ''}\n"
                )
            await message.answer("\n".join(lines))
        finally:
            session.close()

    async def stats(self, message: types.Message):
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
            if not user:
                await message.answer("📈 暂无统计数据")
                return
            monthly = self.service.get_monthly_stats(user.id)
            await message.answer(
                f"📈 {monthly['month']}月统计\n"
                f"总收入: ¥{monthly['total_income']:.2f}\n"
                f"总支出: ¥{monthly['total_expense']:.2f}\n"
                f"结余: ¥{monthly['balance']:.2f}"
            )
        finally:
            session.close()

    async def handle_command(self, message: types.Message):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 记一笔", callback_data="expense_add"),
             InlineKeyboardButton(text="📊 本月统计", callback_data="expense_monthly")],
            [InlineKeyboardButton(text="📈 年度报表", callback_data="expense_annual"),
             InlineKeyboardButton(text="📤 导出数据", callback_data="expense_export")],
            [InlineKeyboardButton(text="❓ 使用帮助", callback_data="expense_help")]
        ])
        await message.answer(
            "💰 <b>记账管理</b>\n\n快速记账: 发送 \"<b>项目 金额</b>\"\n例如: <code>午餐 35.5</code>\n收入: <code>收入 5000 工资</code>",
            reply_markup=keyboard, parse_mode="HTML"
        )
    async def handle(self, message: types.Message):
        if not message.text:
            return
        text = message.text.strip()
        pattern1 = r'^(.+?)\s+([\d,.]+)$'
        pattern2 = r'^([\d,.]+)\s+(.+?)$'
        match = re.match(pattern1, text) or re.match(pattern2, text)
        if not match:
            return
        is_income = '收入' in text or '工资' in text or '奖金' in text
        if re.match(pattern1, text):
            desc = match.group(1)
            amt_str = match.group(2)
        else:
            desc = match.group(2)
            amt_str = match.group(1)
        amt_str = amt_str.replace(',', '')
        try:
            amount = float(amt_str)
        except ValueError:
            await message.answer("❌ 金额格式错误")
            return
        if not is_income:
            amount = -abs(amount)
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
            if not user:
                user = User(telegram_id=message.from_user.id, username=message.from_user.username,
                            first_name=message.from_user.first_name)
                session.add(user)
                session.commit()
            category = self.service.auto_categorize(desc)
            expense = Expense(user_id=user.id, amount=amount, category=category,
                              description=desc[:500], message_id=message.message_id)
            session.add(expense)
            session.commit()
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            total = sum(e.amount for e in session.query(Expense).filter(
                Expense.user_id == user.id, Expense.expense_date >= month_start).all())
            emoji = "💰" if amount > 0 else "💸"
            await message.answer(
                f"{emoji} <b>记账成功</b>\n类型: {'收入' if amount > 0 else '支出'}\n金额: <code>{abs(amount):.2f}</code> 元\n分类: {category}\n本月总计: <code>{total:.2f}</code> 元",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"记账失败: {e}")
            session.rollback()
            await message.answer("❌ 记账失败")
        finally:
            session.close()
    async def handle_callback(self, callback: types.CallbackQuery):
        data = callback.data
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
            if not user:
                await callback.answer("请先发送一条消息")
                return
            if data == "expense_monthly":
                stats = self.service.get_monthly_stats(user.id)
                await callback.message.edit_text(
                    f"📊 <b>{stats['month']}月统计</b>\n总收入: {stats['total_income']:.2f}\n总支出: {stats['total_expense']:.2f}\n结余: {stats['balance']:.2f}\n分类: " + "\n".join(f"{k}: {v:.2f}" for k,v in stats['categories'].items()),
                    parse_mode="HTML"
                )
            elif data == "expense_annual":
                stats = self.service.get_annual_stats(user.id)
                await callback.message.edit_text(
                    f"📈 <b>{stats['year']}年度</b>\n总收入: {stats['total_income']:.2f}\n总支出: {stats['total_expense']:.2f}\n月均: {stats['avg_monthly']:.2f}",
                    parse_mode="HTML"
                )
            elif data == "expense_export":
                csv = self.service.export_csv(user.id)
                await callback.message.answer_document(
                    types.BufferedInputFile(csv.encode('utf-8'), filename=f"expenses_{datetime.utcnow().strftime('%Y%m%d')}.csv"),
                    caption="📤 导出完成"
                )
            elif data == "expense_help":
                await callback.message.edit_text("📖 帮助：发送 '项目 金额' 记账，'收入 金额 说明' 记收入", parse_mode="HTML")
            await callback.answer()
        except Exception as e:
            logger.error(f"回调处理失败: {e}")
            await callback.answer("操作失败")
        finally:
            session.close()
