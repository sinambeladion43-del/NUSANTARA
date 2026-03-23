import sqlite3
import os

DB_PATH = "nusantara.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            player_name TEXT,
            tribe TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            str INTEGER DEFAULT 10,
            agi INTEGER DEFAULT 10,
            int_ INTEGER DEFAULT 10,
            vit INTEGER DEFAULT 10,
            gold INTEGER DEFAULT 100,
            guild_id INTEGER DEFAULT NULL,
            spouse_id INTEGER DEFAULT NULL,
            hunger INTEGER DEFAULT 100,
            thirst INTEGER DEFAULT 100,
            is_banned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            item_type TEXT,
            quantity INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS equipment (
            user_id INTEGER PRIMARY KEY,
            weapon TEXT DEFAULT 'Tangan Kosong',
            armor TEXT DEFAULT 'Baju Biasa',
            accessory TEXT DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            target_monster TEXT,
            target_amount INTEGER,
            reward_exp INTEGER,
            reward_gold INTEGER,
            reward_item TEXT DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS player_quests (
            user_id INTEGER,
            quest_id INTEGER,
            progress INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            claimed INTEGER DEFAULT 0,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, quest_id)
        );

        CREATE TABLE IF NOT EXISTS guilds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            leader_id INTEGER,
            total_power INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS guild_members (
            guild_id INTEGER,
            user_id INTEGER,
            role TEXT DEFAULT 'Prajurit',
            PRIMARY KEY (guild_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS broadcast_users (
            user_id INTEGER PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            detail TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS marriage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id INTEGER,
            player2_id INTEGER,
            married_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            key_name TEXT,
            file_id TEXT,
            uploaded_by INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, key_name)
        );

        CREATE TABLE IF NOT EXISTS gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            gift_type TEXT,
            content TEXT,
            file_id TEXT DEFAULT NULL,
            message TEXT DEFAULT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS pending_proposals (
            proposer_id INTEGER,
            target_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (proposer_id, target_id)
        );

        CREATE TABLE IF NOT EXISTS pending_duels (
            challenger_id INTEGER,
            target_id INTEGER,
            bet INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (challenger_id, target_id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    ''')

    # Insert default quests
    c.execute("SELECT COUNT(*) FROM quests")
    if c.fetchone()[0] == 0:
        default_quests = [
            ("Usir Genderuwo dari Desa", "Kalahkan 3 Genderuwo yang mengganggu desa!", "Genderuwo", 3, 100, 50, None),
            ("Selamatkan Anak dari Wewe Gombel", "Kalahkan 2 Wewe Gombel!", "Wewe Gombel", 2, 80, 40, None),
            ("Hancurkan Leak di Bali", "Kalahkan 5 Leak jahat!", "Leak", 5, 150, 80, None),
            ("Bunuh Naga di Mahakam", "Kalahkan Naga Basuki!", "Naga Basuki", 1, 300, 200, "Ramuan Sakti"),
            ("Taklukkan Buaya Siluman", "Kalahkan 2 Buaya Siluman!", "Buaya Siluman", 2, 120, 70, None),
            ("Buru Kuntilanak", "Kalahkan 4 Kuntilanak!", "Kuntilanak", 4, 90, 45, None),
            ("Singkirkan Buto Ijo", "Kalahkan Buto Ijo yang mengamuk!", "Buto Ijo", 1, 250, 150, "Jimat Keberanian"),
            ("Perburuan Garuda", "Kalahkan 2 Garuda Muda!", "Garuda Muda", 2, 130, 80, None),
        ]
        c.executemany("INSERT INTO quests (title, description, target_monster, target_amount, reward_exp, reward_gold, reward_item) VALUES (?,?,?,?,?,?,?)", default_quests)

    conn.commit()
    conn.close()

def log_activity(user_id, action, detail):
    conn = get_db()
    conn.execute("INSERT INTO activity_logs (user_id, action, detail) VALUES (?,?,?)", (user_id, action, detail))
    conn.commit()
    conn.close()

def get_player(user_id):
    conn = get_db()
    player = conn.execute("SELECT * FROM players WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return player

def is_admin(user_id):
    owner_id = int(os.environ.get('OWNER_ID', 0))
    if user_id == owner_id:
        return True
    conn = get_db()
    result = conn.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return result is not None

def is_maintenance():
    conn = get_db()
    result = conn.execute("SELECT value FROM settings WHERE key='maintenance'").fetchone()
    conn.close()
    return result and result['value'] == 'on'

def get_photo(category, key_name):
    conn = get_db()
    result = conn.execute("SELECT file_id FROM photos WHERE category=? AND key_name=?", (category, key_name)).fetchone()
    conn.close()
    return result['file_id'] if result else None

TRIBE_STATS = {
    "Jawa": {"str": 2, "agi": 0, "int_": 0, "vit": 2},
    "Sunda": {"str": 0, "agi": 3, "int_": 1, "vit": 0},
    "Batak": {"str": 4, "agi": 0, "int_": 0, "vit": 1},
    "Bugis": {"str": 0, "agi": 2, "int_": 2, "vit": 0},
    "Dayak": {"str": 1, "agi": 2, "int_": 2, "vit": 0},
}

MONSTERS = {
    "Genderuwo":    {"hp": 80,  "atk": 15, "def": 5,  "exp": 30,  "gold": 20,  "emoji": "🌑"},
    "Kuntilanak":   {"hp": 60,  "atk": 20, "def": 3,  "exp": 25,  "gold": 15,  "emoji": "👻"},
    "Leak":         {"hp": 100, "atk": 18, "def": 8,  "exp": 40,  "gold": 25,  "emoji": "👿"},
    "Wewe Gombel":  {"hp": 70,  "atk": 12, "def": 6,  "exp": 20,  "gold": 10,  "emoji": "😱"},
    "Naga Basuki":  {"hp": 200, "atk": 30, "def": 15, "exp": 100, "gold": 80,  "emoji": "🐉", "boss": True},
    "Buto Ijo":     {"hp": 150, "atk": 25, "def": 12, "exp": 80,  "gold": 60,  "emoji": "👹", "boss": True},
    "Garuda Muda":  {"hp": 120, "atk": 22, "def": 10, "exp": 60,  "gold": 40,  "emoji": "🦅"},
    "Buaya Siluman":{"hp": 90,  "atk": 18, "def": 12, "exp": 45,  "gold": 30,  "emoji": "🐊"},
    "Nyi Roro Kidul":{"hp":250, "atk": 35, "def": 20, "exp": 150, "gold": 120, "emoji": "🌊", "boss": True},
}

WEAPONS = {
    "Keris Biasa":       {"atk": 5,  "price": 100},
    "Mandau":            {"atk": 10, "price": 250},
    "Trisula":           {"atk": 15, "price": 500},
    "Kujang Sakti":      {"atk": 20, "price": 800},
    "Clurit Berdarah":   {"atk": 18, "price": 700},
    "Keris Pusaka Naga": {"atk": 35, "price": 2000, "rare": True},
}

ARMORS = {
    "Baju Kulit":           {"def": 5,  "price": 80},
    "Perisai Dayak":        {"def": 10, "price": 200},
    "Baju Zirah Majapahit": {"def": 20, "price": 600},
    "Mahkota Prabu":        {"def": 15, "price": 1500, "bonus": {"str":5,"agi":5,"int_":5,"vit":5}, "rare": True},
}

CONSUMABLES = {
    "Ramuan Jamu":        {"heal": 30, "price": 50},
    "Ramuan Sakti":       {"heal": 80, "price": 120},
    "Jimat Keberanian":   {"str_bonus": 5, "price": 80},
    "Jimat Keberuntungan":{"gold_bonus": 0.1, "price": 100},
}

FOODS = {
    "Nasi Putih":   {"hunger": 20, "price": 15,  "emoji": "🍚"},
    "Nasi Goreng":  {"hunger": 35, "price": 30,  "emoji": "🍛"},
    "Sate Ayam":    {"hunger": 40, "price": 40,  "emoji": "🍢"},
    "Rendang":      {"hunger": 60, "price": 70,  "emoji": "🥘"},
    "Nasi Tumpeng": {"hunger": 100,"price": 150, "emoji": "🍱", "special": True},
}

DRINKS = {
    "Air Putih":      {"thirst": 25, "price": 5,   "emoji": "💧"},
    "Teh Tarik":      {"thirst": 40, "price": 20,  "emoji": "🍵"},
    "Es Kelapa Muda": {"thirst": 60, "price": 35,  "emoji": "🥥"},
    "Jus Markisa":    {"thirst": 50, "hp": 10, "price": 50,  "emoji": "🧃"},
    "Jamu Sakti":     {"thirst": 80, "hp": 20, "price": 100, "emoji": "🍶", "special": True},
}

def exp_to_level(level):
    return level * 100

def get_weapon_atk(weapon_name):
    return WEAPONS.get(weapon_name, {}).get("atk", 0)

def get_armor_def(armor_name):
    return ARMORS.get(armor_name, {}).get("def", 0)

def make_progress_bar(current, total, length=10):
    filled = int((current / max(total, 1)) * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"{bar} {current}/{total}"
