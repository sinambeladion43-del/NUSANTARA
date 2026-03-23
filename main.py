import os
import logging
import threading
from flask import Flask, jsonify
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from database import init_db
from handlers.start import start_handler, handle_name_input, choose_tribe
from handlers.profile import profile_handler
from handlers.battle import hunt_handler, battle_action_handler
from handlers.inventory import inventory_handler, equip_handler
from handlers.shop import shop_handler, buy_handler, shop_category_handler
from handlers.food import makan_handler, minum_handler, eat_action_handler
from handlers.quest import quest_handler, claimquest_handler, quest_accept_handler
from handlers.guild import (createguild_handler, joinguild_handler, leaveguild_handler,
                             guildinfo_handler, guildinvite_handler, guildkick_handler,
                             guildwar_handler, topguild_handler)
from handlers.marriage import lamar_handler, cerai_handler, pasangan_handler, marriage_response_handler, divorce_confirm_handler
from handlers.gift import kirimhadiah_handler, hadiah_handler
from handlers.pvp import duel_handler, duel_response_handler
from handlers.daily import daily_handler
from handlers.leaderboard import top_handler
from handlers.rename import rename_handler, rename_confirm_handler
from handlers.admin import (addadmin_handler, removeadmin_handler, ban_handler, unban_handler,
                             resetplayer_handler, givegold_handler, giveitem_handler,
                             setlevel_handler, playerinfo_handler, sethunger_handler,
                             setthirst_handler, forcedivorce_handler, maintenance_handler,
                             announce_handler, addquest_handler, addmonster_handler,
                             serverstats_handler, logs_handler)
from handlers.photo import setphoto_handler, deletephoto_handler, listphotos_handler
from handlers.help import help_handler
from jobs import setup_jobs

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('OWNER_ID', 0))

# Flask app for health check
flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return jsonify({"status": "ok", "game": "Nusantara Chronicles"})

@flask_app.route('/health')
def health_check():
    return jsonify({"status": "running"})

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False)

def main():
    init_db()

    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Flask health check server started")

    app = Application.builder().token(BOT_TOKEN).build()

    # Character
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("profile", profile_handler))
    app.add_handler(CommandHandler("rename", rename_handler))

    # Battle
    app.add_handler(CommandHandler("hunt", hunt_handler))

    # Inventory & Equipment
    app.add_handler(CommandHandler("inventory", inventory_handler))
    app.add_handler(CommandHandler("equip", equip_handler))

    # Shop
    app.add_handler(CommandHandler("shop", shop_handler))
    app.add_handler(CommandHandler("buy", buy_handler))

    # Food & Drink
    app.add_handler(CommandHandler("makan", makan_handler))
    app.add_handler(CommandHandler("minum", minum_handler))
    app.add_handler(CommandHandler("gunakan", eat_action_handler))

    # Quest
    app.add_handler(CommandHandler("quest", quest_handler))
    app.add_handler(CommandHandler("claimquest", claimquest_handler))

    # Guild
    app.add_handler(CommandHandler("createguild", createguild_handler))
    app.add_handler(CommandHandler("joinguild", joinguild_handler))
    app.add_handler(CommandHandler("leaveguild", leaveguild_handler))
    app.add_handler(CommandHandler("guildinfo", guildinfo_handler))
    app.add_handler(CommandHandler("guildinvite", guildinvite_handler))
    app.add_handler(CommandHandler("guildkick", guildkick_handler))
    app.add_handler(CommandHandler("guildwar", guildwar_handler))
    app.add_handler(CommandHandler("topguild", topguild_handler))

    # Marriage
    app.add_handler(CommandHandler("lamar", lamar_handler))
    app.add_handler(CommandHandler("cerai", cerai_handler))
    app.add_handler(CommandHandler("pasangan", pasangan_handler))

    # Gift
    app.add_handler(CommandHandler("kirimhadiah", kirimhadiah_handler))
    app.add_handler(CommandHandler("hadiah", hadiah_handler))

    # PVP
    app.add_handler(CommandHandler("duel", duel_handler))

    # Daily
    app.add_handler(CommandHandler("daily", daily_handler))

    # Leaderboard
    app.add_handler(CommandHandler("top", top_handler))

    # Help
    app.add_handler(CommandHandler("help", help_handler))

    # Admin - Player Management
    app.add_handler(CommandHandler("addadmin", addadmin_handler))
    app.add_handler(CommandHandler("removeadmin", removeadmin_handler))
    app.add_handler(CommandHandler("ban", ban_handler))
    app.add_handler(CommandHandler("unban", unban_handler))
    app.add_handler(CommandHandler("resetplayer", resetplayer_handler))
    app.add_handler(CommandHandler("givegold", givegold_handler))
    app.add_handler(CommandHandler("giveitem", giveitem_handler))
    app.add_handler(CommandHandler("setlevel", setlevel_handler))
    app.add_handler(CommandHandler("playerinfo", playerinfo_handler))
    app.add_handler(CommandHandler("sethunger", sethunger_handler))
    app.add_handler(CommandHandler("setthirst", setthirst_handler))
    app.add_handler(CommandHandler("forcedivorce", forcedivorce_handler))
    app.add_handler(CommandHandler("maintenance", maintenance_handler))
    app.add_handler(CommandHandler("announce", announce_handler))
    app.add_handler(CommandHandler("addquest", addquest_handler))
    app.add_handler(CommandHandler("addmonster", addmonster_handler))
    app.add_handler(CommandHandler("serverstats", serverstats_handler))
    app.add_handler(CommandHandler("logs", logs_handler))

    # Admin - Photo
    app.add_handler(CommandHandler("setphoto", setphoto_handler))
    app.add_handler(CommandHandler("deletephoto", deletephoto_handler))
    app.add_handler(CommandHandler("listphotos", listphotos_handler))

    # Callback query handlers
    app.add_handler(CallbackQueryHandler(choose_tribe, pattern="^tribe_"))
    app.add_handler(CallbackQueryHandler(battle_action_handler, pattern="^battle_"))
    app.add_handler(CallbackQueryHandler(shop_category_handler, pattern="^shop_"))
    app.add_handler(CallbackQueryHandler(eat_action_handler, pattern="^eat_|^drink_"))
    app.add_handler(CallbackQueryHandler(quest_accept_handler, pattern="^quest_"))
    app.add_handler(CallbackQueryHandler(marriage_response_handler, pattern="^marry_"))
    app.add_handler(CallbackQueryHandler(divorce_confirm_handler, pattern="^divorce_"))
    app.add_handler(CallbackQueryHandler(duel_response_handler, pattern="^duel_"))
    app.add_handler(CallbackQueryHandler(rename_confirm_handler, pattern="^rename_"))

    # Message handler for name input
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input))

    # Setup scheduled jobs
    setup_jobs(app)

    logger.info("🏰 Nusantara Chronicles Bot started!")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
