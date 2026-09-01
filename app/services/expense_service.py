from datetime import datetime, timedelta
from app.models.database import get_session, Expense
class ExpenseService:
    CATEGORIES = {
        '餐饮': ['餐','饭','吃','喝','咖啡','奶茶','外卖','食堂','早餐','午餐','晚餐'],
        '交通': ['车','公交','地铁','打车','滴滴','高铁','火车','飞机','油','停车'],
        '购物': ['买','购','淘宝','京东','拼多多','超市','商场','衣服','鞋','包'],
        '娱乐': ['电影','游戏','KTV','旅游','门票','演唱','聚会','酒吧'],
        '住房': ['房租','物业','水电','燃气','维修','装修'],
        '收入': ['工资','奖金','兼职','投资','理财','分红','报销']
    }
    def auto_categorize(self, description: str) -> str:
        desc = description.lower()
        for cat, keywords in self.CATEGORIES.items():
            for kw in keywords:
                if kw in desc:
                    return cat
        return '其他'
    def get_monthly_stats(self, user_id: int):
        session = get_session()
        try:
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            expenses = session.query(Expense).filter(
                Expense.user_id == user_id,
                Expense.expense_date >= month_start,
                Expense.expense_date < month_end
            ).all()
            total_income = sum(e.amount for e in expenses if e.amount > 0)
            total_expense = sum(abs(e.amount) for e in expenses if e.amount < 0)
            categories = {}
            for e in expenses:
                categories[e.category] = categories.get(e.category, 0) + abs(e.amount)
            return {'month': now.month, 'total_income': total_income, 'total_expense': total_expense,
                    'balance': total_income - total_expense, 'categories': categories}
        finally:
            session.close()
    def get_annual_stats(self, user_id: int):
        session = get_session()
        try:
            now = datetime.utcnow()
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            expenses = session.query(Expense).filter(
                Expense.user_id == user_id,
                Expense.expense_date >= year_start
            ).all()
            total_income = sum(e.amount for e in expenses if e.amount > 0)
            total_expense = sum(abs(e.amount) for e in expenses if e.amount < 0)
            monthly = {}
            for e in expenses:
                m = e.expense_date.month
                monthly[m] = monthly.get(m, 0) + abs(e.amount)
            avg = total_expense / 12 if monthly else 0
            return {'year': now.year, 'total_income': total_income, 'total_expense': total_expense,
                    'avg_monthly': avg, 'monthly': monthly}
        finally:
            session.close()
    def export_csv(self, user_id: int) -> str:
        session = get_session()
        try:
            expenses = session.query(Expense).filter(Expense.user_id == user_id).order_by(Expense.expense_date.desc()).all()
            lines = ['日期,类型,金额,分类,描述']
            for e in expenses:
                lines.append(f"{e.expense_date.strftime('%Y-%m-%d %H:%M')},{'收入' if e.amount>0 else '支出'},{abs(e.amount):.2f},{e.category},{e.description}")
            return '\n'.join(lines)
        finally:
            session.close()
