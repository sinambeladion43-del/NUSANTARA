from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, get_player, TRIBE_STATS, log_activity
from middleware import check_player

WAITING_NAME = {}

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)

    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO broadcast_users (user_id) VALUES (?)", (user.id,))
    conn.commit()
    conn.close()

    if player:
        await update.message.reply_text(
            f"⚔️ Selamat datang kembali, *{player['player_name']}*!\n\n"
            f"Gunakan /help untuk melihat daftar perintah.",
            parse_mode="Markdown"
        )
        return

    WAITING_NAME[user.id] = True
    await update.message.reply_text(
        "⚔️ *Selamat datang di Nusantara Chronicles!*\n\n"
        "Dunia mitologi Indonesia menantimu, ksatria!\n\n"
        "Masukkan nama karaktermu (3-20 karakter):",
        parse_mode="Markdown"
    )

async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in WAITING_NAME:
        return

    name = update.message.text.strip()
    if len(name) < 3 or len(name) > 20:
        await update.message.reply_text("❌ Nama harus 3-20 karakter! Coba lagi:")
        return

    import re
    if not re.match(r'^[a-zA-Z0-9 ]+$', name):
        await update.message.reply_text("❌ Nama tidak boleh mengandung karakter spesial! Coba lagi:")
        return

    context.user_data['pending_name'] = name
    del WAITING_NAME[user.id]

    keyboard = [
        [InlineKeyboardButton("🗡️ Jawa", callback_data="tribe_Jawa"),
         InlineKeyboardButton("🏹 Sunda", callback_data="tribe_Sunda")],
        [InlineKeyboardButton("🪓 Batak", callback_data="tribe_Batak"),
         InlineKeyboardButton("⚓ Bugis", callback_data="tribe_Bugis")],
        [InlineKeyboardButton("🌿 Dayak", callback_data="tribe_Dayak")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✨ Nama karaktermu: *{name}*\n\n"
        "Pilih sukumu:\n\n"
        "🗡️ *Jawa* — STR+2, VIT+2 | Ksatria Tangguh\n"
        "🏹 *Sunda* — AGI+3, INT+1 | Penjaga Hutan\n"
        "🪓 *Batak* — STR+4, VIT+1 | Pejuang Gagah\n"
        "⚓ *Bugis* — AGI+2, INT+2 | Pelaut Pemberani\n"
        "🌿 *Dayak* — STR+1, AGI+2, INT+2 | Pendekar Hutan",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def choose_tribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    tribe = query.data.replace("tribe_", "")
    name = context.user_data.get('pending_name', user.first_name)

    bonus = TRIBE_STATS.get(tribe, {})
    base_str = 10 + bonus.get("str", 0)
    base_agi = 10 + bonus.get("agi", 0)
    base_int = 10 + bonus.get("int_", 0)
    base_vit = 10 + bonus.get("vit", 0)

    conn = get_db()
    conn.execute('''
        INSERT OR IGNORE INTO players 
        (user_id, username, player_name, tribe, str, agi, int_, vit)
        VALUES (?,?,?,?,?,?,?,?)
    ''', (user.id, user.username or user.first_name, name, tribe,
          base_str, base_agi, base_int, base_vit))
    conn.execute("INSERT OR IGNORE INTO equipment (user_id) VALUES (?)", (user.id,))
    conn.commit()
    conn.close()

    log_activity(user.id, "register", f"Bergabung sebagai {tribe}: {name}")

    tribe_emojis = {"Jawa":"🗡️","Sunda":"🏹","Batak":"🪓","Bugis":"⚓","Dayak":"🌿"}
    emoji = tribe_emojis.get(tribe, "⚔️")

    await query.edit_message_text(
        f"🎉 *Selamat datang, {name}!*\n\n"
        f"{emoji} Suku: *{tribe}*\n\n"
        f"❤️ HP: 100/100\n"
        f"⚔️ STR: {base_str} | 🏃 AGI: {base_agi}\n"
        f"🔮 INT: {base_int} | 🛡️ VIT: {base_vit}\n"
        f"💰 Kepeng: 100\n\n"
        f"Petualanganmu di Nusantara dimulai!\n"
        f"Gunakan /hunt untuk berburu monster pertamamu! ⚔️",
        parse_mode="Markdown"
    )
