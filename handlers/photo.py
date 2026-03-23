from telegram import Update
from telegram.ext import ContextTypes
from database import get_db, log_activity
from middleware import admin_only, check_player

@admin_only
async def setphoto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format: Reply foto dengan /setphoto [category] [key_name]\n\n"
            "Category: monster, item, quest, background, food, drink\n"
            "Contoh: /setphoto monster genderuwo"
        )
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("❌ Harus reply ke sebuah foto!")
        return

    category = context.args[0].lower()
    key_name = "_".join(context.args[1:]).lower()
    file_id = update.message.reply_to_message.photo[-1].file_id

    valid_categories = ['monster', 'item', 'quest', 'background', 'food', 'drink']
    if category not in valid_categories:
        await update.message.reply_text(f"❌ Category harus salah satu dari: {', '.join(valid_categories)}")
        return

    conn = get_db()
    conn.execute('''INSERT OR REPLACE INTO photos (category, key_name, file_id, uploaded_by)
                    VALUES (?,?,?,?)''', (category, key_name, file_id, user.id))
    conn.commit()
    conn.close()

    log_activity(user.id, "setphoto", f"{category}/{key_name}")
    await update.message.reply_text(
        f"✅ Foto berhasil disimpan!\n📁 Category: {category}\n🔑 Key: {key_name}"
    )

@admin_only
async def deletephoto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ Format: /deletephoto [category] [key_name]")
        return
    category = context.args[0].lower()
    key_name = "_".join(context.args[1:]).lower()
    conn = get_db()
    conn.execute("DELETE FROM photos WHERE category=? AND key_name=?", (category, key_name))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Foto {category}/{key_name} dihapus!")

@admin_only
async def listphotos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    if context.args:
        category = context.args[0].lower()
        photos = conn.execute("SELECT * FROM photos WHERE category=? ORDER BY key_name", (category,)).fetchall()
    else:
        photos = conn.execute("SELECT * FROM photos ORDER BY category, key_name").fetchall()
    conn.close()

    if not photos:
        await update.message.reply_text("📭 Belum ada foto tersimpan!")
        return

    text = "🖼️ *DAFTAR FOTO*\n\n"
    current_cat = ""
    for p in photos:
        if p['category'] != current_cat:
            current_cat = p['category']
            text += f"\n📁 *{current_cat.upper()}*\n"
        text += f"  • {p['key_name']}\n"

    await update.message.reply_text(text, parse_mode="Markdown")
