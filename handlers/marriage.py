import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, get_player, log_activity
from middleware import check_player

# ===== MARRIAGE =====
@check_player
async def lamar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    if player['spouse_id']:
        await update.message.reply_text("❌ Kamu sudah menikah! Cerai dulu dengan /cerai")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply pesan orang yang ingin kamu lamar!")
        return
    target = update.message.reply_to_message.from_user
    if target.id == user.id:
        await update.message.reply_text("❌ Tidak bisa melamar diri sendiri!")
        return
    if player['gold'] < 500:
        await update.message.reply_text("❌ Butuh 500 Kepeng untuk melamar!")
        return
    target_player = get_player(target.id)
    if not target_player:
        await update.message.reply_text("❌ Target belum terdaftar!")
        return
    if target_player['spouse_id']:
        await update.message.reply_text("❌ Target sudah menikah!")
        return

    keyboard = [[InlineKeyboardButton("💍 Terima", callback_data=f"marry_accept_{user.id}"),
                 InlineKeyboardButton("❌ Tolak", callback_data=f"marry_reject_{user.id}")]]
    await update.message.reply_text(
        f"💒 *{player['player_name']}* melamarmu!\n\nApakah kamu menerima?",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def marriage_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    if "accept" in data:
        proposer_id = int(data.split("_")[-1])
        proposer = get_player(proposer_id)
        target = get_player(user.id)
        if not proposer or not target:
            await query.edit_message_text("❌ Data tidak ditemukan!")
            return
        conn = get_db()
        conn.execute("UPDATE players SET spouse_id=?, gold=gold-500, max_hp=max_hp+10, hp=MIN(max_hp+10,hp+10), str=str+5, agi=agi+5, int_=int_+5, vit=vit+5 WHERE user_id=?", (user.id, proposer_id))
        conn.execute("UPDATE players SET spouse_id=?, max_hp=max_hp+10, hp=MIN(max_hp+10,hp+10), str=str+5, agi=agi+5, int_=int_+5, vit=vit+5 WHERE user_id=?", (proposer_id, user.id))
        conn.execute("INSERT INTO marriage (player1_id, player2_id) VALUES (?,?)", (proposer_id, user.id))
        conn.commit()
        conn.close()
        await query.edit_message_text(
            f"💒 *{proposer['player_name']}* dan *{target['player_name']}* resmi menikah!\n\n💑 Semoga bahagia di Nusantara Chronicles! 💕\n\n✨ Bonus: +10 Max HP, +5 semua stat!",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("💔 Lamaran ditolak...")

@check_player
async def cerai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    if not player['spouse_id']:
        await update.message.reply_text("❌ Kamu belum menikah!")
        return
    keyboard = [[InlineKeyboardButton("✅ Ya, Cerai", callback_data="divorce_confirm"),
                 InlineKeyboardButton("❌ Batal", callback_data="divorce_cancel")]]
    await update.message.reply_text(
        "💔 Yakin ingin bercerai? Biaya: 300 Kepeng\n\nBonus pernikahan akan hilang!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def divorce_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if query.data == "divorce_cancel":
        await query.edit_message_text("✅ Perceraian dibatalkan.")
        return
    player = get_player(user.id)
    if player['gold'] < 300:
        await query.edit_message_text("❌ Kepengmu tidak cukup! Butuh 300 Kepeng.")
        return
    conn = get_db()
    spouse_id = player['spouse_id']
    conn.execute("UPDATE players SET spouse_id=NULL, gold=gold-300, max_hp=max_hp-10, str=str-5, agi=agi-5, int_=int_-5, vit=vit-5 WHERE user_id=?", (user.id,))
    conn.execute("UPDATE players SET spouse_id=NULL, max_hp=max_hp-10, str=str-5, agi=agi-5, int_=int_-5, vit=vit-5 WHERE user_id=?", (spouse_id,))
    conn.commit()
    conn.close()
    await query.edit_message_text("💔 Perceraian telah dilakukan. -300 Kepeng")

@check_player
async def pasangan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    if not player['spouse_id']:
        await update.message.reply_text("💔 Kamu belum menikah!")
        return
    spouse = get_player(player['spouse_id'])
    if not spouse:
        await update.message.reply_text("❌ Data pasangan tidak ditemukan!")
        return
    await update.message.reply_text(
        f"💑 *Pasanganmu:*\n\n👤 {spouse['player_name']}\n🏯 {spouse['tribe']}\n⭐ Level {spouse['level']}\n❤️ HP: {spouse['hp']}/{spouse['max_hp']}",
        parse_mode="Markdown"
    )
