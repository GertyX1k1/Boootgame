import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_conn()) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT,
            race TEXT,
            class TEXT,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            atk INTEGER DEFAULT 10,
            df INTEGER DEFAULT 5,
            gold INTEGER DEFAULT 50,
            gems INTEGER DEFAULT 0,
            guild_id INTEGER,
            banned INTEGER DEFAULT 0,
            last_daily TEXT,
            last_explore TEXT,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_id TEXT,
            item_name TEXT,
            item_type TEXT,
            power INTEGER DEFAULT 0,
            qty INTEGER DEFAULT 1,
            equipped INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS guilds (
            guild_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            owner_id INTEGER,
            level INTEGER DEFAULT 1,
            gold INTEGER DEFAULT 0
        );
        """)
        conn.commit()


def now():
    return datetime.now(timezone.utc).isoformat()


# ---------- USERS ----------

def get_user(user_id: int):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def create_user(user_id: int, username: str, name: str, race: str, cls: str, hp: int, atk: int, df: int):
    with closing(get_conn()) as conn:
        conn.execute(
            "INSERT INTO users (user_id, username, name, race, class, hp, max_hp, atk, df, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, name, race, cls, hp, hp, atk, df, now())
        )
        conn.commit()


def update_user(user_id: int, **fields):
    if not fields:
        return
    keys = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [user_id]
    with closing(get_conn()) as conn:
        conn.execute(f"UPDATE users SET {keys} WHERE user_id=?", values)
        conn.commit()


def all_user_ids():
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT user_id FROM users WHERE banned=0").fetchall()
        return [r["user_id"] for r in rows]


def get_top(limit=10):
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT user_id, name, level, xp, wins FROM users WHERE banned=0 "
            "ORDER BY level DESC, xp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def stats():
    with closing(get_conn()) as conn:
        total = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        banned = conn.execute("SELECT COUNT(*) c FROM users WHERE banned=1").fetchone()["c"]
        top_level = conn.execute("SELECT MAX(level) m FROM users").fetchone()["m"] or 0
        total_gold = conn.execute("SELECT SUM(gold) s FROM users").fetchone()["s"] or 0
        return {"total": total, "banned": banned, "top_level": top_level, "total_gold": total_gold}


# ---------- INVENTORY ----------

def add_item(user_id: int, item_id: str, name: str, item_type: str, power: int, qty: int = 1):
    with closing(get_conn()) as conn:
        existing = conn.execute(
            "SELECT id, qty FROM inventory WHERE user_id=? AND item_id=? AND equipped=0",
            (user_id, item_id)
        ).fetchone()
        if existing and item_type == "potion":
            conn.execute("UPDATE inventory SET qty=qty+? WHERE id=?", (qty, existing["id"]))
        else:
            conn.execute(
                "INSERT INTO inventory (user_id, item_id, item_name, item_type, power, qty) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, item_id, name, item_type, power, qty)
            )
        conn.commit()


def get_inventory(user_id: int):
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT * FROM inventory WHERE user_id=?", (user_id,)).fetchall()
        return [dict(r) for r in rows]


def equip_item(user_id: int, inv_id: int, item_type: str):
    with closing(get_conn()) as conn:
        conn.execute(
            "UPDATE inventory SET equipped=0 WHERE user_id=? AND item_type=?",
            (user_id, item_type)
        )
        conn.execute("UPDATE inventory SET equipped=1 WHERE id=?", (inv_id,))
        conn.commit()


def consume_potion(inv_id: int):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT qty FROM inventory WHERE id=?", (inv_id,)).fetchone()
        if not row:
            return
        if row["qty"] <= 1:
            conn.execute("DELETE FROM inventory WHERE id=?", (inv_id,))
        else:
            conn.execute("UPDATE inventory SET qty=qty-1 WHERE id=?", (inv_id,))
        conn.commit()


def remove_inventory_item(inv_id: int):
    with closing(get_conn()) as conn:
        conn.execute("DELETE FROM inventory WHERE id=?", (inv_id,))
        conn.commit()


# ---------- GUILDS ----------

def create_guild(name: str, owner_id: int):
    with closing(get_conn()) as conn:
        cur = conn.execute("INSERT INTO guilds (name, owner_id) VALUES (?, ?)", (name, owner_id))
        conn.commit()
        return cur.lastrowid


def get_guild(guild_id: int):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM guilds WHERE guild_id=?", (guild_id,)).fetchone()
        return dict(row) if row else None


def get_guild_by_name(name: str):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT * FROM guilds WHERE name=?", (name,)).fetchone()
        return dict(row) if row else None


def guild_members(guild_id: int):
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT user_id, name, level FROM users WHERE guild_id=? ORDER BY level DESC", (guild_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def top_guilds(limit=10):
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT g.guild_id, g.name, COUNT(u.user_id) members, COALESCE(SUM(u.level),0) power "
            "FROM guilds g LEFT JOIN users u ON u.guild_id = g.guild_id "
            "GROUP BY g.guild_id ORDER BY power DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
