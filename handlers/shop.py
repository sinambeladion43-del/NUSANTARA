from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_db, get_player, WEAPONS, ARMORS, CONSUMABLES, FOODS, DRINKS, log_activity
from middleware import check_player

@check_player
async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚔️ Senjata", callback_data="shop_weapon"),
         InlineKeyboardButton("🛡️ Armor", callback_data="shop_armor")],
        [InlineKeyboardButton("🧪 Consumable", callback_data="shop_consumable"),
         InlineKeyboardButton("🍽️ Makanan", callback_data="shop_food")],
        [InlineKeyboardButton("💧 Minuman", callback_data="shop_drink")],
    ]
    player = get_player(update.effective_user.id)
    await update.message.reply_text(
        f"🏪 *TOKO NUSANTARA*\n\n"
        f"💰 Kepengmu: {player['gold']}\n\n"
        f"Pilih kategori:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def shop_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("shop_", "")
    player = get_player(query.from_user.id)

    text = f"🏪 *TOKO - {category.upper()}*\n\n"
    text += f"💰 Kepengmu: {player['gold']}\n\n"

    if category == "weapon":
        for name, data in WEAPONS.items():
            rare = " 💎 RARE" if data.get('rare') else ""
            text += f"🗡️ *{name}*{rare}\n   ATK +{data['atk']} | Harga: {data['price']} Kepeng\n\n"
    elif category == "armor":
        for name, data in ARMORS.items():
            rare = " 💎 RARE" if data.get('rare') else ""
            text += f"🛡️ *{name}*{rare}\n   DEF +{data['def']} | Harga: {data['price']} Kepeng\n\n"
    elif category == "consumable":
        for name, data in CONSUMABLES.items():
            text += f"🧪 *{name}*\n   Harga: {data['price']} Kepeng\n\n"
    elif category == "food":
        for name, data in FOODS.items():
            special = " ⭐ SPECIAL" if data.get('special') else ""
            text += f"{data['emoji']} *{name}*{special}\n   Lapar +{data['hunger']} | Harga: {data['price']} Kepeng\n\n"
    elif category == "drink":
        for name, data in DRINKS.items():
            special = " ⭐ SPECIAL" if data.get('special') else ""
            text += f"{data['emoji']} *{name}*{special}\n   Haus +{data['thirst']} | Harga: {data['price']} Kepeng\n\n"

    text += "Gunakan /buy [nama_item] untuk membeli!"
    await query.edit_message_text(text, parse_mode="Markdown")

@check_player
async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("❌ Format: /buy [nama_item]")
        return

    item_name = " ".join(context.args)
    player = get_player(user.id)

    # Find item in all categories
    all_items = {}
    for name, data in WEAPONS.items():
        all_items[name] = {"price": data['price'], "type": "weapon"}
    for name, data in ARMORS.items():
        all_items[name] = {"price": data['price'], "type": "armor"}
    for name, data in CONSUMABLES.items():
        all_items[name] = {"price": data['price'], "type": "consumable"}
    for name, data in FOODS.items():
        all_items[name] = {"price": data['price'], "type": "food"}
    for name, data in DRINKS.items():
        all_items[name] = {"price": data['price'], "type": "drink"}

    if item_name not in all_items:
        await update.message.reply_text(f"❌ Item *{item_name}* tidak ditemukan di toko!", parse_mode="Markdown")
        return

    item = all_items[item_name]
    if player['gold'] < item['price']:
        await update.message.reply_text(f"❌ Kepengmu tidak cukup! Butuh {item['price']} Kepeng.")
        return

    conn = get_db()
    conn.execute("UPDATE players SET gold=gold-? WHERE user_id=?", (item['price'], user.id))
    existing = conn.execute("SELECT * FROM inventory WHERE user_id=? AND item_name=?", (user.id, item_name)).fetchone()
    if existing:
        conn.execute("UPDATE inventory SET quantity=quantity+1 WHERE user_id=? AND item_name=?", (user.id, item_name))
    else:
        conn.execute("INSERT INTO inventory (user_id, item_name, item_type) VALUES (?,?,?)",
                    (user.id, item_name, item['type']))
    conn.commit()
    conn.close()

    log_activity(user.id, "buy", f"Membeli {item_name}")
    await update.message.reply_text(
        f"✅ Berhasil membeli *{item_name}*!\n💰 -{item['price']} Kepeng",
        parse_mode="Markdown"
    )
