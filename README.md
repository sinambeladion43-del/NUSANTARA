# ⚔️ Nusantara Chronicles Bot

Bot RPG Telegram bertema mitologi Indonesia!

## 🚀 Cara Setup

### 1. Clone / Upload ke GitHub
Upload semua file ini ke repository GitHub kamu.

### 2. Import ke Replit
- Buka replit.com
- Klik **+ Create Repl**
- Pilih **Import from GitHub**
- Pilih repo kamu

### 3. Set Environment Variables
Di Replit, buka tab **Secrets** dan tambahkan:
```
BOT_TOKEN = token_dari_botfather
OWNER_ID  = telegram_user_id_kamu
```

**Cara dapat BOT_TOKEN:**
1. Buka Telegram → cari @BotFather
2. Ketik /newbot
3. Ikuti instruksi → copy token

**Cara dapat OWNER_ID:**
1. Buka Telegram → cari @userinfobot
2. Ketik /start → copy angka User ID

### 4. Deploy
- Klik **Run** untuk test
- Klik **Deploy** → pilih **Reserved VM** untuk Always On 24/7

---

## 📋 Fitur

| Fitur | Command |
|-------|---------|
| Buat karakter | /start |
| Lihat profil | /profile |
| Ganti nama | /rename |
| Berburu monster | /hunt |
| Inventori | /inventory |
| Pasang equipment | /equip |
| Toko | /shop |
| Beli item | /buy |
| Makan | /makan |
| Minum | /minum |
| Quest harian | /quest |
| Klaim quest | /claimquest |
| Buat guild | /createguild |
| Gabung guild | /joinguild |
| Info guild | /guildinfo |
| Melamar | /lamar |
| Cerai | /cerai |
| Lihat pasangan | /pasangan |
| Kirim hadiah | /kirimhadiah |
| Inbox hadiah | /hadiah |
| Duel PVP | /duel |
| Hadiah harian | /daily |
| Leaderboard | /top |
| Bantuan | /help |

## 👑 Admin Commands

| Command | Fungsi |
|---------|--------|
| /addadmin [id] | Tambah admin |
| /ban [id] [alasan] | Ban player |
| /unban [id] | Unban player |
| /givegold [id] [jumlah] | Beri Kepeng |
| /giveitem [id] [item] [qty] | Beri item |
| /setlevel [id] [level] | Set level |
| /playerinfo [id] | Info player |
| /resetplayer [id] | Reset data |
| /maintenance on/off | Maintenance mode |
| /announce [pesan] | Broadcast pesan |
| /serverstats | Statistik server |
| /setphoto [cat] [key] | Set foto (reply foto) |
| /listphotos | Daftar foto |

## 🖼️ Cara Set Foto

1. Kirim foto ke bot
2. Reply foto tersebut dengan:
   ```
   /setphoto monster genderuwo
   /setphoto food nasi_goreng
   /setphoto background profile
   ```

Category yang tersedia: `monster`, `item`, `quest`, `background`, `food`, `drink`

---

Made with ❤️ — Nusantara Chronicles
