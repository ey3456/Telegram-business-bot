# Telegram Business Bot

企业版 Telegram 机器人：消息记录、防撤回/防编辑、记账、TTS，以及 Flask 管理后台。

## 运行步骤

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 复制 `.env.example` 为 `.env`，填写真实的 `BOT_TOKEN`（从 [@BotFather](https://t.me/BotFather) 获取）和 `BUSINESS_USER_ID`（通过 [@userinfobot](https://t.me/userinfobot) 获取）。

3. 初始化数据库（启动时也会自动创建）：

```bash
python -c "from app.models.database import init_db; init_db()"
```

4. 启动服务：

```bash
python run.py
```

5. 在 Telegram 中进入「设置 → Telegram Business → 聊天机器人」，输入 Bot 用户名。

6. 管理后台：访问 `http://localhost:5000`，默认用户名 `admin`，密码在 `.env` 的 `ADMIN_PASSWORD` 中配置。
