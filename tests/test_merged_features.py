import os
import unittest

os.environ.setdefault("BOT_TOKEN", "0:test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


class ExpenseServiceTests(unittest.TestCase):
    def test_auto_categorize(self):
        from app.services.expense_service import ExpenseService

        service = ExpenseService()
        self.assertEqual(service.auto_categorize("午餐外卖"), "餐饮")
        self.assertEqual(service.auto_categorize("地铁通勤"), "交通")
        self.assertEqual(service.auto_categorize("未知项目"), "其他")


class AutoReplyParseTests(unittest.TestCase):
    def test_keyword_split(self):
        raw = "你好 | 您好！有什么可以帮您的？"
        keyword, reply = raw.split("|", 1)
        self.assertEqual(keyword.strip(), "你好")
        self.assertEqual(reply.strip(), "您好！有什么可以帮您的？")


class AdminGateTests(unittest.TestCase):
    def test_admin_zero_denied(self):
        from app.config import Config
        from app.services.auth import is_admin

        Config.ADMIN_ID = 0
        Config.BUSINESS_USER_ID = 0
        self.assertFalse(is_admin(0))
        Config.ADMIN_ID = 42
        self.assertTrue(is_admin(42))
        self.assertFalse(is_admin(7))


if __name__ == "__main__":
    unittest.main()
