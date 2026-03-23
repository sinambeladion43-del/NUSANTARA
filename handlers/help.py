from telegram import Update
from telegram.ext import ContextTypes
from middleware import check_player

@check_player
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚔️ *NUSANTARA CHRONICLES*\n"
        "📜 Daftar Perintah\n\n"

        "👤 *KARAKTER*\n"
        "/start — Mulai & buat karakter\n"
        "/profile — Lihat profil\n"
        "/rename [nama] — Ganti nama (200 Kepeng)\n\n"

        "⚔️ *PERTEMPURAN*\n"
        "/hunt — Berburu monster\n"
        "/duel @user [taruhan] — Tantang duel\n\n"

        "🎒 *INVENTORI*\n"
        "/inventory — Lihat item\n"
        "/equip [item] — Pasang senjata/armor\n"
        "/gunakan [item] — Pakai item\n\n"

        "🍽️ *KEBUTUHAN*\n"
        "/makan — Beli & makan\n"
        "/minum — Beli & minum\n\n"

        "🏪 *TOKO*\n"
        "/shop — Buka toko\n"
        "/buy [item] — Beli item\n\n"

        "📜 *QUEST*\n"
        "/quest — Lihat quest harian\n"
        "/claimquest — Klaim reward quest\n\n"

        "🏰 *GUILD*\n"
        "/createguild [nama] — Buat guild (500 Kepeng)\n"
        "/joinguild [nama] — Gabung guild\n"
        "/leaveguild — Keluar guild\n"
        "/guildinfo — Info guild\n"
        "/topguild — Ranking guild\n\n"

        "💑 *PERNIKAHAN*\n"
        "/lamar — Reply pesan untuk melamar\n"
        "/cerai — Ajukan cerai\n"
        "/pasangan — Lihat info pasangan\n\n"

        "🎁 *HADIAH*\n"
        "/kirimhadiah @user gold [jumlah]\n"
        "/kirimhadiah @user item [nama] [qty]\n"
        "Reply foto + /kirimhadiah untuk kirim foto\n"
        "/hadiah — Lihat hadiah masuk\n\n"

        "🏆 *LEADERBOARD*\n"
        "/top — Top 10 player\n"
        "/topguild — Top 10 guild\n\n"

        "🎁 *LAINNYA*\n"
        "/daily — Hadiah harian\n"
        "/help — Tampilkan bantuan ini"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
