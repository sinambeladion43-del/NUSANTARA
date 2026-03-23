import random
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, get_player, get_weapon_atk, get_armor_def, log_activity
from middleware import check_player

# ===== PVP =====
duel_cooldowns = {}

@check_player
async def duel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    now = time.time()
    if user.id in duel_cooldowns and now - duel_cooldowns[user.id] < 300:
        remaining = int(300 - (now - duel_cooldowns[user.id]))
        await update.message.reply_text(f"⏳ Tunggu {remaining} detik lagi!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply pesan orang yang ingin kamu duel!")
        return
    target = update.message.reply_to_message.from_user
    if target.id == user.id:
        await update.message.reply_text("❌ Tidak bisa duel diri sendiri!")
        return
    bet = int(context.args[0]) if context.args and context.args[0].isdigit() else 0
    player = get_player(user.id)
    if bet > 0 and player['gold'] < bet:
        await update.message.reply_text("❌ Kepengmu tidak cukup untuk taruhan!")
        return
    keyboard = [[InlineKeyboardButton("✅ Terima", callback_data=f"duel_accept_{user.id}_{bet}"),
                 InlineKeyboardButton("❌ Tolak", callback_data=f"duel_reject_{user.id}")]]
    bet_text = f"\n💰 Taruhan: {bet} Kepeng" if bet > 0 else ""
    await update.message.reply_text(
        f"⚔️ *{player['player_name']}* menantangmu duel!{bet_text}\n\nApakah kamu menerima?",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def duel_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data.split("_")

    if data[1] == "reject":
        await query.edit_message_text("❌ Tantangan duel ditolak.")
        return

    challenger_id = int(data[2])
    bet = int(data[3]) if len(data) > 3 else 0
    challenger = get_player(challenger_id)
    target = get_player(user.id)

    if not challenger or not target:
        await query.edit_message_text("❌ Data tidak ditemukan!")
        return

    conn = get_db()
    c_equip = conn.execute("SELECT * FROM equipment WHERE user_id=?", (challenger_id,)).fetchone()
    t_equip = conn.execute("SELECT * FROM equipment WHERE user_id=?", (user.id,)).fetchone()
    conn.close()

    c_power = challenger['str'] + challenger['agi'] + get_weapon_atk(c_equip['weapon'] if c_equip else '') + random.randint(1,20)
    t_power = target['str'] + target['agi'] + get_weapon_atk(t_equip['weapon'] if t_equip else '') + random.randint(1,20)

    if c_power >= t_power:
        winner, loser = challenger, target
        winner_id, loser_id = challenger_id, user.id
    else:
        winner, loser = target, challenger
        winner_id, loser_id = user.id, challenger_id

    duel_cooldowns[challenger_id] = time.time()

    conn = get_db()
    if bet > 0:
        conn.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (bet, winner_id))
        conn.execute("UPDATE players SET gold=gold-? WHERE user_id=?", (bet, loser_id))
    conn.commit()
    conn.close()

    log_activity(winner_id, "duel_win", f"Menang duel vs {loser['player_name']}")
    bet_result = f"\n💰 +{bet} Kepeng untuk {winner['player_name']}!" if bet > 0 else ""

    await query.edit_message_text(
        f"⚔️ *HASIL DUEL*\n\n"
        f"🏆 Pemenang: *{winner['player_name']}*\n"
        f"💀 Kalah: *{loser['player_name']}*\n\n"
        f"Power: {c_power} vs {t_power}{bet_result}",
        parse_mode="Markdown"
    )

# ===== DAILY =====
@check_player
async def daily_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_db()
    result = conn.execute("SELECT value FROM settings WHERE key=?", (f"daily_{user.id}",)).fetchone()

    now = datetime.now()
    if result:
        last = datetime.fromisoformat(result['value'])
        if now - last < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last)
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            conn.close()
            await update.message.reply_text(f"⏳ Sudah klaim hari ini!\nTunggu {hours}j {minutes}m lagi.")
            return

    gold = random.randint(50, 200)
    conn.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (gold, user.id))
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (f"daily_{user.id}", now.isoformat()))
    conn.commit()
    conn.close()

    log_activity(user.id, "daily", f"+{gold} Kepeng")
    await update.message.reply_text(f"🎁 *Hadiah Harian!*\n\n💰 +{gold} Kepeng\n\nKembali lagi besok!", parse_mode="Markdown")

# ===== LEADERBOARD =====
@check_player
async def top_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    players = conn.execute("SELECT player_name, tribe, level, exp FROM players WHERE is_banned=0 ORDER BY level DESC, exp DESC LIMIT 10").fetchall()
    conn.close()
    text = "🏆 *TOP 10 PLAYER*\n\n"
    medals = ["👑","🥈","🥉"]
    tribe_emojis = {"Jawa":"🗡️","Sunda":"🏹","Batak":"🪓","Bugis":"⚓","Dayak":"🌿"}
    for i, p in enumerate(players):
        medal = medals[i] if i < 3 else f"{i+1}."
        emoji = tribe_emojis.get(p['tribe'], "⚔️")
        text += f"{medal} {emoji} *{p['player_name']}* — Level {p['level']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ===== RENAME =====
rename_cooldowns = {}

@check_player
async def rename_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("❌ Format: /rename [nama_baru]")
        return
    new_name = " ".join(context.args).strip()
    if len(new_name) < 3 or len(new_name) > 20:
        await update.message.reply_text("❌ Nama harus 3-20 karakter!")
        return
    import re
    if not re.match(r'^[a-zA-Z0-9 ]+$', new_name):
        await update.message.reply_text("❌ Nama tidak boleh mengandung karakter spesial!")
        return

    now = time.time()
    if user.id in rename_cooldowns and now - rename_cooldowns[user.id] < 604800:
        remaining = int(604800 - (now - rename_cooldowns[user.id]))
        days = remaining // 86400
        await update.message.reply_text(f"⏳ Bisa rename lagi dalam {days} hari!")
        return

    player = get_player(user.id)
    if player['gold'] < 200:
        await update.message.reply_text("❌ Butuh 200 Kepeng untuk ganti nama!")
        return

    context.user_data['rename_to'] = new_name
    keyboard = [[InlineKeyboardButton("✅ Ya", callback_data="rename_confirm"),
                 InlineKeyboardButton("❌ Batal", callback_data="rename_cancel")]]
    await update.message.reply_text(
        f"Ganti nama dari *{player['player_name']}* → *{new_name}*?\nBiaya: 200 Kepeng",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def rename_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if query.data == "rename_cancel":
        await query.edit_message_text("✅ Ganti nama dibatalkan.")
        return
    new_name = context.user_data.get('rename_to')
    if not new_name:
        await query.edit_message_text("❌ Sesi expired. Coba lagi!")
        return
    conn = get_db()
    conn.execute("UPDATE players SET player_name=?, gold=gold-200 WHERE user_id=?", (new_name, user.id))
    conn.commit()
    conn.close()
    rename_cooldowns[user.id] = time.time()
    log_activity(user.id, "rename", f"Ganti nama ke {new_name}")
    await query.edit_message_text(f"✅ Nama berhasil diganti ke *{new_name}*!\n💰 -200 Kepeng", parse_mode="Markdown")
