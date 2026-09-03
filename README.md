# Telegram 统一机器人

将原先分散的四个能力合并到同一个 Bot 进程：

1. **企业会话**（`telegram-business-bot` / `tg-secretary`）：Business 消息入库、连接管理
2. **防撤回 / 防编辑**：记录删除与编辑前后内容
3. **记账 + 管理后台**：命令记账、自然语言记账、Flask 后台
4. **多功能运营**（`tg_bot`）：频道搬运、自动回复、群发、订阅说明，以及 TTS

Telegram 对同一 Token 只允许一个 `getUpdates` 长轮询，因此必须合并为单一 Dispatcher。

## 运行

```bash
pip install -r requirements.txt
cp .env.example .env
# 填写 BOT_TOKEN、BUSINESS_USER_ID、ADMIN_ID
python run.py
```

管理后台：`http://localhost:5000`（用户名 `ADMIN_USERNAME`，密码 `ADMIN_PASSWORD`）。

## 命令

| 命令 | 说明 |
|------|------|
| `/start` `/menu` `/help` | 欢迎、菜单、帮助 |
| `/expense` `/addexpense` `/expenses` `/stats` | 记账 |
| `/tts 文本` | 文字转语音 |
| `/addforward` `/listforward` | 搬运（管理员） |
| `/addreply` `/listreply` | 自动回复 |
| `/broadcast` | 群发到库中用户（管理员） |
| `/pricing` `/subscribe` | 订阅说明 |

普通文本会按顺序尝试：自动回复 → 群/频道搬运 → `项目 金额` 记账。

## 环境变量

见 `.env.example`。`ADMIN_ID` 控制搬运与群发权限；未设置时回退到 `BUSINESS_USER_ID`。

## 测试

```bash
python -m unittest discover -s tests -v
```
