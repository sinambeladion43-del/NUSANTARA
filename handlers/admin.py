import os
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db, get_player, is_admin, log_activity
from middleware import admin_only

@admin_only
async def addadmin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Format: /addadmin [user_id]")
        return
    owner_id = int(os.environ.get('OWNER_ID', 0))
    if update.effective_user.id != owner_id:
        await update.message.reply_text("❌ Hanya owner yang bisa menambah admin!")
        return
    target_id = int(context.args[0])
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?,?)", (target_id, update.effective_user.id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ User {target_id} ditambah sebagai admin!")

@admin_only
async def removeadmin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    target_id = int(context.args[0])
    conn = get_db()
    conn.execute("DELETE FROM admins WHERE user_id=?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Admin {target_id} dihapus!")

@admin_only
async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    target_id = int(context.args[0])
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Tidak ada alasan"
    conn = get_db()
    conn.execute("UPDATE players SET is_banned=1 WHERE user_id=?", (target_id,))
    conn.commit()
    conn.close()
    log_activity(target_id, "banned", reason)
    await update.message.reply_text(f"⛔ User {target_id} dibanned!\nAlasan: {reason}")

@admin_only
async def unban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    target_id = int(context.args[0])
    conn = get_db()
    conn.execute("UPDATE players SET is_banned=0 WHERE user_id=?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ User {target_id} di-unban!")

@admin_only
async def resetplayer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    target_id = int(context.args[0])
    conn = get_db()
    conn.execute("DELETE FROM players WHERE user_id=?", (target_id,))
    conn.execute("DELETE FROM inventory WHERE user_id=?", (target_id,))
    conn.execute("DELETE FROM equipment WHERE user_id=?", (target_id,))
    conn.execute("DELETE FROM player_quests WHERE user_id=?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Data player {target_id} direset!")

@admin_only
async def givegold_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2: return
    target_id, amount = int(context.args[0]), int(context.args[1])
    conn = get_db()
    conn.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (amount, target_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ +{amount} Kepeng diberikan ke {target_id}!")

@admin_only
async def giveitem_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3: return
    target_id = int(context.args[0])
    qty = int(context.args[-1])
    item_name = " ".join(context.args[1:-1])
    conn = get_db()
    existing = conn.execute("SELECT * FROM inventory WHERE user_id=? AND item_name=?", (target_id, item_name)).fetchone()
    if existing:
        conn.execute("UPDATE inventory SET quantity=quantity+? WHERE user_id=? AND item_name=?", (qty, target_id, item_name))
    else:
        conn.execute("INSERT INTO inventory (user_id, item_name, item_type, quantity) VALUES (?,?,'item',?)", (target_id, item_name, qty))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ {qty}x {item_name} diberikan ke {target_id}!")

@admin_only
async def setlevel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2: return
    target_id, level = int(context.args[0]), int(context.args[1])
    conn = get_db()
    conn.execute("UPDATE players SET level=?, exp=0 WHERE user_id=?", (level, target_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Level {target_id} diset ke {level}!")

@admin_only
async def playerinfo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    target_id = int(context.args[0])
    player = get_player(target_id)
    if not player:
        await update.message.reply_text("❌ Player tidak ditemukan!")
        return
    await update.message.reply_text(
        f"👤 *INFO PLAYER {target_id}*\n\n"
        f"Nama: {player['player_name']}\nSuku: {player['tribe']}\n"
        f"Level: {player['level']} | EXP: {player['exp']}\n"
        f"HP: {player['hp']}/{player['max_hp']}\n"
        f"Gold: {player['gold']}\nBanned: {'Ya' if player['is_banned'] else 'Tidak'}\n"
        f"Hunger: {player['hunger']} | Thirst: {player['thirst']}",
        parse_mode="Markdown"
    )

@admin_only
async def sethunger_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2: return
    target_id, val = int(context.args[0]), int(context.args[1])
    conn = get_db()
    conn.execute("UPDATE players SET hunger=? WHERE user_id=?", (min(100,max(0,val)), target_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Hunger {target_id} diset ke {val}!")

@admin_only
async def setthirst_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2: return
    target_id, val = int(context.args[0]), int(context.args[1])
    conn = get_db()
    conn.execute("UPDATE players SET thirst=? WHERE user_id=?", (min(100,max(0,val)), target_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Thirst {target_id} diset ke {val}!")

@admin_only
async def forcedivorce_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    target_id = int(context.args[0])
    player = get_player(target_id)
    if not player or not player['spouse_id']:
        await update.message.reply_text("❌ Player tidak punya pasangan!")
        return
    conn = get_db()
    conn.execute("UPDATE players SET spouse_id=NULL WHERE user_id=? OR user_id=?", (target_id, player['spouse_id']))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Perceraian paksa {target_id} berhasil!")

@admin_only
async def maintenance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    mode = context.args[0]
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('maintenance', ?)", (mode,))
    conn.commit()
    conn.close()
    status = "ON 🔧" if mode == "on" else "OFF ✅"
    await update.message.reply_text(f"Maintenance mode: {status}")

@admin_only
async def announce_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    msg = " ".join(context.args)
    conn = get_db()
    users = conn.execute("SELECT user_id FROM broadcast_users").fetchall()
    conn.close()
    success = 0
    for u in users:
        try:
            await context.bot.send_message(u['user_id'], f"📢 *PENGUMUMAN*\n\n{msg}", parse_mode="Markdown")
            success += 1
        except: pass
    await update.message.reply_text(f"✅ Pesan terkirim ke {success}/{len(users)} player!")

@admin_only
async def addquest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    parts = " ".join(context.args).split("|")
    if len(parts) < 6: return
    title, desc, monster, amount, exp, gold = parts[0], parts[1], parts[2], int(parts[3]), int(parts[4]), int(parts[5])
    conn = get_db()
    conn.execute("INSERT INTO quests (title, description, target_monster, target_amount, reward_exp, reward_gold) VALUES (?,?,?,?,?,?)",
                (title, desc, monster, amount, exp, gold))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Quest *{title}* ditambahkan!", parse_mode="Markdown")

@admin_only
async def addmonster_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Fitur addmonster akan segera hadir!")

@admin_only
async def serverstats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as c FROM players").fetchone()['c']
    banned = conn.execute("SELECT COUNT(*) as c FROM players WHERE is_banned=1").fetchone()['c']
    guilds = conn.execute("SELECT COUNT(*) as c FROM guilds").fetchone()['c']
    married = conn.execute("SELECT COUNT(*) as c FROM marriage").fetchone()['c']
    conn.close()
    await update.message.reply_text(
        f"📊 *SERVER STATS*\n\n"
        f"👥 Total Player: {total}\n"
        f"⛔ Dibanned: {banned}\n"
        f"🏰 Total Guild: {guilds}\n"
        f"💑 Pasangan Menikah: {married}",
        parse_mode="Markdown"
    )

@admin_only
async def logs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    target_id = int(context.args[0])
    conn = get_db()
    logs = conn.execute("SELECT * FROM activity_logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 10", (target_id,)).fetchall()
    conn.close()
    if not logs:
        await update.message.reply_text("❌ Tidak ada log!")
        return
    text = f"📋 *LOG PLAYER {target_id}*\n\n"
    for l in logs:
        text += f"• [{l['timestamp'][:16]}] {l['action']}: {l['detail']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")
