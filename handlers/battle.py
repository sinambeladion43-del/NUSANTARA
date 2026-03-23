import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (get_db, get_player, get_photo, MONSTERS, log_activity,
                      get_weapon_atk, get_armor_def, exp_to_level)
from middleware import check_player

hunt_cooldowns = {}
active_battles = {}

@check_player
async def hunt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user.id)
    if not player:
        await update.message.reply_text("❌ Kamu belum terdaftar! Ketik /start")
        return

    # Cooldown check
    now = time.time()
    if user.id in hunt_cooldowns and now - hunt_cooldowns[user.id] < 30:
        remaining = int(30 - (now - hunt_cooldowns[user.id]))
        await update.message.reply_text(f"⏳ Tunggu {remaining} detik lagi sebelum berburu!")
        return

    # Hunger/thirst check
    if player['hunger'] < 20 or player['thirst'] < 20:
        await update.message.reply_text(
            "⚠️ Karaktermu terlalu lapar/haus!\n"
            "Gunakan /makan dan /minum dulu sebelum berburu!"
        )
        return

    # Check HP
    if player['hp'] <= 0:
        await update.message.reply_text("💀 HP kamu habis! Gunakan /makan atau beli ramuan untuk memulihkan HP.")
        return

    hunt_cooldowns[user.id] = now

    # Reduce hunger/thirst
    conn = get_db()
    conn.execute("UPDATE players SET hunger=MAX(0,hunger-10), thirst=MAX(0,thirst-8) WHERE user_id=?", (user.id,))
    conn.commit()

    # Pick random monster
    monster_name = random.choice(list(MONSTERS.keys()))
    monster_data = MONSTERS[monster_name].copy()
    monster_hp = monster_data['hp']

    active_battles[user.id] = {
        "monster_name": monster_name,
        "monster_hp": monster_hp,
        "monster_max_hp": monster_hp,
        "monster_data": monster_data,
        "player_hp": player['hp'],
        "turn": 1
    }

    equip = conn.execute("SELECT * FROM equipment WHERE user_id=?", (user.id,)).fetchone()
    conn.close()

    weapon_atk = get_weapon_atk(equip['weapon'] if equip else '')
    armor_def = get_armor_def(equip['armor'] if equip else '')

    is_boss = monster_data.get('boss', False)
    boss_tag = " 👑 BOSS" if is_boss else ""

    text = (
        f"⚔️ *PERTEMPURAN DIMULAI!*{boss_tag}\n\n"
        f"{monster_data['emoji']} *{monster_name}*\n"
        f"❤️ HP Monster: {monster_hp}/{monster_hp}\n\n"
        f"👤 *{player['player_name']}*\n"
        f"❤️ HP Kamu: {player['hp']}/{player['max_hp']}\n\n"
        f"Pilih aksimu:"
    )

    keyboard = [
        [InlineKeyboardButton("⚔️ Serang", callback_data="battle_attack"),
         InlineKeyboardButton("🔮 Sihir", callback_data="battle_magic")],
        [InlineKeyboardButton("🛡️ Bertahan", callback_data="battle_defend"),
         InlineKeyboardButton("🏃 Kabur", callback_data="battle_run")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    photo_file_id = get_photo("monster", monster_name.lower().replace(" ", "_"))
    if photo_file_id:
        await update.message.reply_photo(photo=photo_file_id, caption=text,
                                          parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

@check_player
async def battle_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if user.id not in active_battles:
        await query.edit_message_text("❌ Tidak ada pertempuran aktif!")
        return

    battle = active_battles[user.id]
    action = query.data.replace("battle_", "")
    player = get_player(user.id)

    conn = get_db()
    equip = conn.execute("SELECT * FROM equipment WHERE user_id=?", (user.id,)).fetchone()
    conn.close()

    weapon_atk = get_weapon_atk(equip['weapon'] if equip else '')
    armor_def = get_armor_def(equip['armor'] if equip else '')

    monster = battle['monster_data']
    monster_name = battle['monster_name']
    player_hp = battle['player_hp']
    monster_hp = battle['monster_hp']

    player_dmg = 0
    monster_dmg = 0
    defend_mode = False
    log_text = ""

    if action == "attack":
        player_dmg = max(1, player['str'] + weapon_atk - monster['def'])
        player_dmg += random.randint(-2, 5)
        monster_hp -= player_dmg
        log_text = f"⚔️ Kamu menyerang {monster_name} -{player_dmg} HP!"

    elif action == "magic":
        if player_hp <= 15:
            await query.answer("HP kamu terlalu sedikit untuk menggunakan sihir!", show_alert=True)
            return
        player_dmg = max(1, int(player['int_'] * 1.5) - monster['def'])
        player_hp -= 10
        monster_hp -= player_dmg
        log_text = f"🔮 Kamu menggunakan sihir! -{player_dmg} HP monster, -10 HP kamu!"

    elif action == "defend":
        defend_mode = True
        log_text = "🛡️ Kamu bersiap bertahan..."

    elif action == "run":
        if random.random() < 0.5:
            del active_battles[user.id]
            await query.edit_message_text("🏃 Kamu berhasil kabur dari pertempuran!")
            return
        else:
            log_text = "🏃 Gagal kabur!"

    # Monster attacks
    if monster_hp > 0 and action != "run":
        base_dmg = max(1, monster['atk'] - armor_def)
        if defend_mode:
            base_dmg = base_dmg // 2
        monster_dmg = base_dmg + random.randint(-2, 3)
        monster_dmg = max(1, monster_dmg)
        player_hp -= monster_dmg
        log_text += f"\n{monster['emoji']} {monster_name} menyerang! -{monster_dmg} HP kamu!"

    battle['player_hp'] = player_hp
    battle['monster_hp'] = monster_hp

    # Check win/lose
    if monster_hp <= 0:
        del active_battles[user.id]
        exp_gain = monster['exp']
        gold_gain = monster['gold'] + random.randint(0, 10)

        conn = get_db()
        p = conn.execute("SELECT * FROM players WHERE user_id=?", (user.id,)).fetchone()
        new_exp = p['exp'] + exp_gain
        new_level = p['level']
        level_up_text = ""

        while new_exp >= exp_to_level(new_level):
            new_exp -= exp_to_level(new_level)
            new_level += 1
            level_up_text = f"\n🎉 *LEVEL UP! Level {new_level}!*"

        conn.execute('''UPDATE players SET exp=?, level=?, gold=gold+?, hp=? 
                       WHERE user_id=?''',
                    (new_exp, new_level, gold_gain, max(1, player_hp), user.id))
        conn.commit()

        # Update quest progress
        quests = conn.execute('''SELECT pq.quest_id, q.target_monster, q.target_amount, pq.progress
                                 FROM player_quests pq JOIN quests q ON pq.quest_id=q.id
                                 WHERE pq.user_id=? AND pq.completed=0''', (user.id,)).fetchall()
        for quest in quests:
            if quest['target_monster'] == monster_name:
                new_progress = quest['progress'] + 1
                completed = 1 if new_progress >= quest['target_amount'] else 0
                conn.execute("UPDATE player_quests SET progress=?, completed=? WHERE user_id=? AND quest_id=?",
                            (new_progress, completed, user.id, quest['quest_id']))
        conn.commit()
        conn.close()

        log_activity(user.id, "hunt_win", f"Mengalahkan {monster_name}")

        await query.edit_message_text(
            f"🏆 *MENANG!*\n\n"
            f"{log_text}\n\n"
            f"✅ {monster_name} dikalahkan!\n"
            f"💰 +{gold_gain} Kepeng\n"
            f"⭐ +{exp_gain} EXP{level_up_text}",
            parse_mode="Markdown"
        )
        return

    if player_hp <= 0:
        del active_battles[user.id]
        conn = get_db()
        conn.execute("UPDATE players SET hp=1 WHERE user_id=?", (user.id,))
        conn.commit()
        conn.close()

        log_activity(user.id, "hunt_lose", f"Kalah dari {monster_name}")

        await query.edit_message_text(
            f"💀 *KALAH!*\n\n"
            f"{log_text}\n\n"
            f"Kamu dikalahkan oleh {monster_name}!\n"
            f"HP tersisa 1. Gunakan /makan untuk pulih.",
            parse_mode="Markdown"
        )
        return

    # Continue battle
    conn = get_db()
    conn.execute("UPDATE players SET hp=? WHERE user_id=?", (player_hp, user.id))
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("⚔️ Serang", callback_data="battle_attack"),
         InlineKeyboardButton("🔮 Sihir", callback_data="battle_magic")],
        [InlineKeyboardButton("🛡️ Bertahan", callback_data="battle_defend"),
         InlineKeyboardButton("🏃 Kabur", callback_data="battle_run")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"⚔️ *PERTEMPURAN - Giliran {battle['turn']+1}*\n\n"
        f"{log_text}\n\n"
        f"{monster['emoji']} HP Monster: {max(0,monster_hp)}/{battle['monster_max_hp']}\n"
        f"❤️ HP Kamu: {max(0,player_hp)}/{player['max_hp']}\n\n"
        f"Pilih aksimu:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    battle['turn'] += 1
