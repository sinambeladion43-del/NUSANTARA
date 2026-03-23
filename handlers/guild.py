from telegram import Update
from telegram.ext import ContextTypes
from database import get_db, get_player, log_activity
from middleware import check_player

@check_player
async def createguild_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    if player['guild_id']:
        await update.message.reply_text("❌ Kamu sudah berada di guild!")
        return
    if not context.args:
        await update.message.reply_text("❌ Format: /createguild [nama]")
        return
    name = " ".join(context.args)
    if player['gold'] < 500:
        await update.message.reply_text("❌ Butuh 500 Kepeng untuk membuat guild!")
        return
    conn = get_db()
    try:
        conn.execute("INSERT INTO guilds (name, leader_id) VALUES (?,?)", (name, user.id))
        guild_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("UPDATE players SET guild_id=?, gold=gold-500 WHERE user_id=?", (guild_id, user.id))
        conn.execute("INSERT INTO guild_members (guild_id, user_id, role) VALUES (?,?,?)", (guild_id, user.id, "Pemimpin"))
        conn.commit()
        conn.close()
        log_activity(user.id, "guild_create", f"Membuat guild {name}")
        await update.message.reply_text(f"🏰 Guild *{name}* berhasil dibuat!\n💰 -500 Kepeng", parse_mode="Markdown")
    except:
        conn.close()
        await update.message.reply_text("❌ Nama guild sudah digunakan!")

@check_player
async def joinguild_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    if player['guild_id']:
        await update.message.reply_text("❌ Kamu sudah di guild! Keluar dulu dengan /leaveguild")
        return
    if not context.args:
        await update.message.reply_text("❌ Format: /joinguild [nama]")
        return
    name = " ".join(context.args)
    conn = get_db()
    guild = conn.execute("SELECT * FROM guilds WHERE name=?", (name,)).fetchone()
    if not guild:
        conn.close()
        await update.message.reply_text(f"❌ Guild *{name}* tidak ditemukan!", parse_mode="Markdown")
        return
    conn.execute("UPDATE players SET guild_id=? WHERE user_id=?", (guild['id'], user.id))
    conn.execute("INSERT OR IGNORE INTO guild_members (guild_id, user_id, role) VALUES (?,?,?)", (guild['id'], user.id, "Prajurit"))
    conn.commit()
    conn.close()
    log_activity(user.id, "guild_join", f"Bergabung ke {name}")
    await update.message.reply_text(f"🏰 Kamu bergabung ke guild *{name}*!", parse_mode="Markdown")

@check_player
async def leaveguild_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    if not player['guild_id']:
        await update.message.reply_text("❌ Kamu tidak berada di guild!")
        return
    conn = get_db()
    conn.execute("DELETE FROM guild_members WHERE guild_id=? AND user_id=?", (player['guild_id'], user.id))
    conn.execute("UPDATE players SET guild_id=NULL WHERE user_id=?", (user.id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("🚪 Kamu keluar dari guild.")

@check_player
async def guildinfo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    if not player['guild_id']:
        await update.message.reply_text("❌ Kamu tidak berada di guild!")
        return
    conn = get_db()
    guild = conn.execute("SELECT * FROM guilds WHERE id=?", (player['guild_id'],)).fetchone()
    members = conn.execute('''SELECT p.player_name, gm.role, p.level FROM guild_members gm
                              JOIN players p ON gm.user_id=p.user_id WHERE gm.guild_id=?
                              ORDER BY p.level DESC''', (guild['id'],)).fetchall()
    conn.close()
    text = f"🏰 *{guild['name']}*\n\n👥 Anggota ({len(members)}):\n"
    for m in members:
        text += f"  • {m['player_name']} — {m['role']} (Lv.{m['level']})\n"
    await update.message.reply_text(text, parse_mode="Markdown")

@check_player
async def guildinvite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fitur invite akan segera hadir!")

@check_player
async def guildkick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fitur kick akan segera hadir!")

@check_player
async def guildwar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚔️ Fitur guild war akan segera hadir!")

@check_player
async def topguild_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    guilds = conn.execute('''SELECT g.name, p.player_name as leader, COUNT(gm.user_id) as members,
                             SUM(pl.level) as power FROM guilds g
                             JOIN players p ON g.leader_id=p.user_id
                             JOIN guild_members gm ON g.id=gm.guild_id
                             JOIN players pl ON gm.user_id=pl.user_id
                             GROUP BY g.id ORDER BY power DESC LIMIT 10''').fetchall()
    conn.close()
    text = "🏆 *TOP GUILD*\n\n"
    medals = ["👑","🥈","🥉"]
    for i, g in enumerate(guilds):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} *{g['name']}* — {g['members']} anggota | Power: {g['power']}\n    Leader: {g['leader']}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")
