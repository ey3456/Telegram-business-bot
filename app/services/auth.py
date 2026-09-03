from app.config import Config


def is_admin(user_id: int) -> bool:
    if user_id == 0:
        return False
    return user_id in {Config.ADMIN_ID, Config.BUSINESS_USER_ID}
