from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, get_player, WEAPONS, ARMORS, CONSUMABLES, log_activity
from middleware import check_player

@check_player
async def inventory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_db()
    items = conn.execute("SELECT * FROM inventory WHERE user_id=? ORDER BY item_type", (user.id,)).fetchall()
    equip = conn.execute("SELECT * FROM equipment WHERE user_id=?", (user.id,)).fetchone()
    conn.close()

    if not items:
        await update.message.reply_text("🎒 Inventorimu kosong!\nBeli item di /shop")
        return

    text = "🎒 *INVENTORI*\n\n"
    current_type = ""
    type_emojis = {"weapon":"⚔️","armor":"🛡️","consumable":"🧪","food":"🍽️","drink":"💧"}

    for item in items:
        if item['item_type'] != current_type:
            current_type = item['item_type']
            emoji = type_emojis.get(current_type, "📦")
            text += f"\n{emoji} *{current_type.upper()}*\n"

        equipped = ""
        if equip:
            if equip['weapon'] == item['item_name'] or equip['armor'] == item['item_name']:
                equipped = " ✅"
        text += f"• {item['item_name']} x{item['quantity']}{equipped}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

@check_player
async def equip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("❌ Format: /equip [nama_item]")
        return

    item_name = " ".join(context.args)
    conn = get_db()
    item = conn.execute("SELECT * FROM inventory WHERE user_id=? AND item_name=?", (user.id, item_name)).fetchone()

    if not item:
        conn.close()
        await update.message.reply_text(f"❌ Kamu tidak punya *{item_name}*!", parse_mode="Markdown")
        return

    if item['item_type'] == 'weapon':
        conn.execute("UPDATE equipment SET weapon=? WHERE user_id=?", (item_name, user.id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"⚔️ Kamu memasang *{item_name}*!", parse_mode="Markdown")
    elif item['item_type'] == 'armor':
        conn.execute("UPDATE equipment SET armor=? WHERE user_id=?", (item_name, user.id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"🛡️ Kamu memakai *{item_name}*!", parse_mode="Markdown")
    else:
        conn.close()
        await update.message.reply_text("❌ Item ini tidak bisa di-equip!")
