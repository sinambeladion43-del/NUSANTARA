import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, get_player, log_activity
from middleware import check_player

@check_player
async def quest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_db()

    # Get or assign quests
    active = conn.execute('''SELECT pq.*, q.title, q.description, q.target_monster, q.target_amount, 
                             q.reward_exp, q.reward_gold, q.reward_item
                             FROM player_quests pq JOIN quests q ON pq.quest_id=q.id
                             WHERE pq.user_id=? AND pq.claimed=0''', (user.id,)).fetchall()

    if not active:
        # Assign 3 random quests
        all_quests = conn.execute("SELECT * FROM quests").fetchall()
        chosen = random.sample(all_quests, min(3, len(all_quests)))
        for q in chosen:
            conn.execute("INSERT OR IGNORE INTO player_quests (user_id, quest_id) VALUES (?,?)", (user.id, q['id']))
        conn.commit()
        active = conn.execute('''SELECT pq.*, q.title, q.description, q.target_monster, q.target_amount,
                                 q.reward_exp, q.reward_gold, q.reward_item
                                 FROM player_quests pq JOIN quests q ON pq.quest_id=q.id
                                 WHERE pq.user_id=? AND pq.claimed=0''', (user.id,)).fetchall()

    conn.close()
    text = "📜 *QUEST HARIAN*\n\n"
    for q in active:
        status = "✅ SELESAI!" if q['completed'] else f"📊 {q['progress']}/{q['target_amount']}"
        text += (f"📌 *{q['title']}*\n"
                 f"   {q['description']}\n"
                 f"   Status: {status}\n"
                 f"   🏆 Reward: {q['reward_exp']} EXP + {q['reward_gold']} Kepeng\n\n")

    text += "Gunakan /claimquest untuk klaim quest yang selesai!"
    await update.message.reply_text(text, parse_mode="Markdown")

@check_player
async def claimquest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_db()
    completed = conn.execute('''SELECT pq.*, q.title, q.reward_exp, q.reward_gold, q.reward_item
                                FROM player_quests pq JOIN quests q ON pq.quest_id=q.id
                                WHERE pq.user_id=? AND pq.completed=1 AND pq.claimed=0''', (user.id,)).fetchall()
    if not completed:
        conn.close()
        await update.message.reply_text("❌ Tidak ada quest yang bisa diklaim!")
        return

    total_exp = sum(q['reward_exp'] for q in completed)
    total_gold = sum(q['reward_gold'] for q in completed)
    for q in completed:
        conn.execute("UPDATE player_quests SET claimed=1 WHERE user_id=? AND quest_id=?", (user.id, q['quest_id']))
    conn.execute("UPDATE players SET exp=exp+?, gold=gold+? WHERE user_id=?", (total_exp, total_gold, user.id))
    conn.commit()
    conn.close()

    log_activity(user.id, "quest_claim", f"+{total_exp} EXP +{total_gold} Kepeng")
    await update.message.reply_text(
        f"🎉 *Quest Diklaim!*\n\n⭐ +{total_exp} EXP\n💰 +{total_gold} Kepeng",
        parse_mode="Markdown"
    )

async def quest_accept_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
