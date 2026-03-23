from telegram import Update
from telegram.ext import ContextTypes
from database import get_db, get_player, get_photo, make_progress_bar, exp_to_level, log_activity
from middleware import check_player

@check_player
async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    if not player:
        await update.message.reply_text("❌ Kamu belum terdaftar! Ketik /start")
        return

    conn = get_db()
    equip = conn.execute("SELECT * FROM equipment WHERE user_id=?", (user.id,)).fetchone()

    guild_name = "Tidak ada"
    if player['guild_id']:
        guild = conn.execute("SELECT name FROM guilds WHERE id=?", (player['guild_id'],)).fetchone()
        if guild:
            guild_name = guild['name']

    spouse_name = "Lajang 💔"
    if player['spouse_id']:
        spouse = conn.execute("SELECT player_name FROM players WHERE user_id=?", (player['spouse_id'],)).fetchone()
        if spouse:
            spouse_name = f"{spouse['player_name']} 💑"

    conn.close()

    hunger = player['hunger']
    thirst = player['thirst']

    def status_emoji(val):
        if val >= 80: return "😊"
        if val >= 50: return "😐"
        if val >= 20: return "😟"
        return "😵"

    exp_needed = exp_to_level(player['level'])
    exp_bar = make_progress_bar(player['exp'], exp_needed)

    weapon = equip['weapon'] if equip else 'Tangan Kosong'
    armor = equip['armor'] if equip else 'Baju Biasa'

    text = (
        f"👤 *{player['player_name']}*\n"
        f"🏯 Suku: {player['tribe']}\n\n"
        f"⭐ Level {player['level']} | EXP: {exp_bar}\n"
        f"❤️ HP: {player['hp']}/{player['max_hp']}\n\n"
        f"🍚 Lapar: {status_emoji(hunger)} {hunger}/100\n"
        f"💧 Haus: {status_emoji(thirst)} {thirst}/100\n\n"
        f"⚔️ STR: {player['str']} | 🏃 AGI: {player['agi']}\n"
        f"🔮 INT: {player['int_']} | 🛡️ VIT: {player['vit']}\n\n"
        f"💰 Kepeng: {player['gold']}\n"
        f"👫 Pasangan: {spouse_name}\n"
        f"🏰 Guild: {guild_name}\n\n"
        f"🗡️ Senjata: {weapon}\n"
        f"🛡️ Armor: {armor}"
    )

    photo_file_id = get_photo("background", f"profile_{player['tribe'].lower()}")
    if not photo_file_id:
        photo_file_id = get_photo("background", "profile")

    if photo_file_id:
        await update.message.reply_photo(photo=photo_file_id, caption=text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

    log_activity(user.id, "profile", "Melihat profil")
