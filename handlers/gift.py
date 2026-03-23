import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, get_player, log_activity
from middleware import check_player

# ===== GIFT =====
@check_player
async def kirimhadiah_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)

    if update.message.reply_to_message and update.message.reply_to_message.photo:
        target = update.message.reply_to_message.from_user
        if target.id == user.id:
            await update.message.reply_text("❌ Tidak bisa kirim hadiah ke diri sendiri!")
            return
        file_id = update.message.reply_to_message.photo[-1].file_id
        msg = " ".join(context.args) if context.args else ""
        conn = get_db()
        conn.execute("INSERT INTO gifts (sender_id, receiver_id, gift_type, file_id, message) VALUES (?,?,?,?,?)",
                    (user.id, target.id, "photo", file_id, msg))
        conn.commit()
        conn.close()
        await context.bot.send_photo(chat_id=target.id, photo=file_id,
                                      caption=f"💝 Hadiah foto dari *{player['player_name']}*!\n💬 {msg}" if msg else f"💝 Hadiah foto dari *{player['player_name']}*!",
                                      parse_mode="Markdown")
        await update.message.reply_text("✅ Hadiah foto berhasil dikirim!")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ Format:\n/kirimhadiah @username gold [jumlah]\n/kirimhadiah @username item [nama] [qty]\nAtau reply foto dengan /kirimhadiah @username [pesan]")
        return

    target_username = context.args[0].replace("@","")
    gift_type = context.args[1]

    conn = get_db()
    target_player = conn.execute("SELECT * FROM players WHERE username=?", (target_username,)).fetchone()
    if not target_player:
        conn.close()
        await update.message.reply_text("❌ Player tidak ditemukan!")
        return

    if target_player['user_id'] == user.id:
        conn.close()
        await update.message.reply_text("❌ Tidak bisa kirim hadiah ke diri sendiri!")
        return

    if gift_type == "gold":
        amount = int(context.args[2]) if len(context.args) > 2 else 0
        if amount < 10:
            conn.close()
            await update.message.reply_text("❌ Minimum kirim 10 Kepeng!")
            return
        if player['gold'] < amount:
            conn.close()
            await update.message.reply_text("❌ Kepengmu tidak cukup!")
            return
        conn.execute("UPDATE players SET gold=gold-? WHERE user_id=?", (amount, user.id))
        conn.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (amount, target_player['user_id']))
        conn.execute("INSERT INTO gifts (sender_id, receiver_id, gift_type, content) VALUES (?,?,?,?)",
                    (user.id, target_player['user_id'], "gold", str(amount)))
        conn.commit()
        conn.close()
        await context.bot.send_message(target_player['user_id'], f"💰 *{player['player_name']}* mengirimkan {amount} Kepeng untukmu!", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Berhasil kirim {amount} Kepeng ke *{target_player['player_name']}*!", parse_mode="Markdown")

    elif gift_type == "item":
        item_name = " ".join(context.args[2:-1]) if len(context.args) > 3 else context.args[2] if len(context.args) > 2 else ""
        qty = int(context.args[-1]) if len(context.args) > 3 else 1
        inv = conn.execute("SELECT * FROM inventory WHERE user_id=? AND item_name=?", (user.id, item_name)).fetchone()
        if not inv or inv['quantity'] < qty:
            conn.close()
            await update.message.reply_text("❌ Item tidak cukup di inventori!")
            return
        conn.execute("UPDATE inventory SET quantity=quantity-? WHERE user_id=? AND item_name=?", (qty, user.id, item_name))
        existing = conn.execute("SELECT * FROM inventory WHERE user_id=? AND item_name=?", (target_player['user_id'], item_name)).fetchone()
        if existing:
            conn.execute("UPDATE inventory SET quantity=quantity+? WHERE user_id=? AND item_name=?", (qty, target_player['user_id'], item_name))
        else:
            conn.execute("INSERT INTO inventory (user_id, item_name, item_type, quantity) VALUES (?,?,?,?)",
                        (target_player['user_id'], item_name, inv['item_type'], qty))
        conn.commit()
        conn.close()
        await context.bot.send_message(target_player['user_id'], f"🎁 *{player['player_name']}* mengirimkan {qty}x *{item_name}* untukmu!", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Berhasil kirim {qty}x *{item_name}*!", parse_mode="Markdown")
    else:
        conn.close()
        await update.message.reply_text("❌ Tipe hadiah tidak valid! Gunakan: gold atau item")

@check_player
async def hadiah_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_db()
    gifts = conn.execute("SELECT g.*, p.player_name FROM gifts g JOIN players p ON g.sender_id=p.user_id WHERE g.receiver_id=? AND g.is_read=0", (user.id,)).fetchall()
    conn.execute("UPDATE gifts SET is_read=1 WHERE receiver_id=?", (user.id,))
    conn.commit()
    conn.close()
    if not gifts:
        await update.message.reply_text("📭 Tidak ada hadiah baru!")
        return
    text = "🎁 *HADIAH MASUK*\n\n"
    for g in gifts:
        if g['gift_type'] == 'gold':
            text += f"💰 Dari *{g['player_name']}*: {g['content']} Kepeng\n"
        elif g['gift_type'] == 'item':
            text += f"🎁 Dari *{g['player_name']}*: {g['content']}\n"
        elif g['gift_type'] == 'photo':
            text += f"📸 Dari *{g['player_name']}*: Foto\n"
    await update.message.reply_text(text, parse_mode="Markdown")
