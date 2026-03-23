from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, get_player, FOODS, DRINKS, log_activity
from middleware import check_player

@check_player
async def makan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = get_player(update.effective_user.id)
    text = f"🍽️ *MENU MAKANAN*\n\n💰 Kepengmu: {player['gold']}\n🍚 Lapar: {player['hunger']}/100\n\n"
    keyboard = []
    for name, data in FOODS.items():
        special = "⭐" if data.get('special') else ""
        text += f"{data['emoji']} *{name}* {special}\n   +{data['hunger']} Lapar | {data['price']} Kepeng\n\n"
        keyboard.append([InlineKeyboardButton(f"{data['emoji']} {name} - {data['price']} Kpg", callback_data=f"eat_{name}")])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

@check_player
async def minum_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = get_player(update.effective_user.id)
    text = f"💧 *MENU MINUMAN*\n\n💰 Kepengmu: {player['gold']}\n💧 Haus: {player['thirst']}/100\n\n"
    keyboard = []
    for name, data in DRINKS.items():
        special = "⭐" if data.get('special') else ""
        text += f"{data['emoji']} *{name}* {special}\n   +{data['thirst']} Haus | {data['price']} Kepeng\n\n"
        keyboard.append([InlineKeyboardButton(f"{data['emoji']} {name} - {data['price']} Kpg", callback_data=f"drink_{name}")])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def eat_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    player = get_player(user.id)
    data = query.data

    if data.startswith("eat_"):
        item_name = data.replace("eat_", "")
        item = FOODS.get(item_name)
        if not item:
            await query.edit_message_text("❌ Makanan tidak ditemukan!")
            return
        if player['gold'] < item['price']:
            await query.answer("❌ Kepengmu tidak cukup!", show_alert=True)
            return
        conn = get_db()
        conn.execute("UPDATE players SET gold=gold-?, hunger=MIN(100,hunger+?) WHERE user_id=?",
                    (item['price'], item['hunger'], user.id))
        conn.commit()
        conn.close()
        log_activity(user.id, "eat", f"Makan {item_name}")
        await query.edit_message_text(f"🍽️ Kamu makan *{item_name}*!\n🍚 +{item['hunger']} Lapar\n💰 -{item['price']} Kepeng", parse_mode="Markdown")

    elif data.startswith("drink_"):
        item_name = data.replace("drink_", "")
        item = DRINKS.get(item_name)
        if not item:
            await query.edit_message_text("❌ Minuman tidak ditemukan!")
            return
        if player['gold'] < item['price']:
            await query.answer("❌ Kepengmu tidak cukup!", show_alert=True)
            return
        conn = get_db()
        hp_bonus = item.get('hp', 0)
        conn.execute("UPDATE players SET gold=gold-?, thirst=MIN(100,thirst+?), hp=MIN(max_hp,hp+?) WHERE user_id=?",
                    (item['price'], item['thirst'], hp_bonus, user.id))
        conn.commit()
        conn.close()
        log_activity(user.id, "drink", f"Minum {item_name}")
        hp_text = f"\n❤️ +{hp_bonus} HP" if hp_bonus else ""
        await query.edit_message_text(f"💧 Kamu minum *{item_name}*!\n💧 +{item['thirst']} Haus{hp_text}\n💰 -{item['price']} Kepeng", parse_mode="Markdown")

@check_player
async def gunakan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Gunakan /makan atau /minum untuk mengonsumsi item!")
