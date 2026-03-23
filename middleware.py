from database import get_player, is_maintenance, is_admin, get_db, log_activity
from functools import wraps

def check_player(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user = update.effective_user
        if not user:
            return

        # Register to broadcast list
        conn = get_db()
        conn.execute("INSERT OR IGNORE INTO broadcast_users (user_id) VALUES (?)", (user.id,))
        conn.commit()
        conn.close()

        # Check maintenance
        if is_maintenance() and not is_admin(user.id):
            await update.effective_message.reply_text("🔧 Bot sedang maintenance. Tunggu sebentar ya!")
            return

        # Check ban
        player = get_player(user.id)
        if player and player['is_banned']:
            await update.effective_message.reply_text("⛔ Kamu telah dibanned dari Nusantara Chronicles.")
            return

        return await func(update, context, *args, **kwargs)
    return wrapper

def admin_only(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user = update.effective_user
        if not is_admin(user.id):
            await update.effective_message.reply_text("❌ Perintah ini hanya untuk admin!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
