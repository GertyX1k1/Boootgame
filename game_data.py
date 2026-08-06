RACES = {
    "human":  {"name": "🧑 Человек",  "hp": 10, "atk": 2, "df": 2},
    "orc":    {"name": "🟢 Орк",      "hp": 20, "atk": 4, "df": -1},
    "elf":    {"name": "🧝 Эльф",     "hp": 0,  "atk": 3, "df": 3},
    "dwarf":  {"name": "🪓 Дворф",    "hp": 15, "atk": 1, "df": 4},
}

CLASSES = {
    "warrior": {"name": "⚔️ Воин",   "hp": 30, "atk": 5, "df": 3, "skill": "Мощный удар (x2 урон)"},
    "mage":    {"name": "🔮 Маг",     "hp": 10, "atk": 9, "df": 0, "skill": "Огненный шар (игнор. защиту)"},
    "rogue":   {"name": "🗡️ Разбойник", "hp": 18, "atk": 7, "df": 1, "skill": "Двойной удар"},
    "cleric":  {"name": "✨ Жрец",    "hp": 22, "atk": 4, "df": 2, "skill": "Исцеление (+30% HP)"},
}

# Монстры для /explore: имя, эмодзи, мин.уровень, hp, atk, df, награда золота, награда опыта
MONSTERS = [
    {"name": "Дикий волк",        "emoji": "🐺", "min_lvl": 1,  "hp": 25,  "atk": 5,  "df": 1, "gold": (5, 12),  "xp": 10},
    {"name": "Гоблин-разведчик",  "emoji": "👺", "min_lvl": 1,  "hp": 30,  "atk": 6,  "df": 2, "gold": (8, 15),  "xp": 14},
    {"name": "Гигантский паук",   "emoji": "🕷️", "min_lvl": 3,  "hp": 45,  "atk": 8,  "df": 2, "gold": (12, 22), "xp": 22},
    {"name": "Скелет-воин",       "emoji": "💀", "min_lvl": 5,  "hp": 60,  "atk": 10, "df": 4, "gold": (18, 30), "xp": 32},
    {"name": "Тролль болотный",   "emoji": "👹", "min_lvl": 8,  "hp": 90,  "atk": 14, "df": 5, "gold": (28, 45), "xp": 48},
    {"name": "Огненный элементаль","emoji": "🔥", "min_lvl": 12, "hp": 120, "atk": 18, "df": 6, "gold": (40, 65), "xp": 70},
    {"name": "Древний дракон",    "emoji": "🐉", "min_lvl": 18, "hp": 220, "atk": 28, "df": 10, "gold": (80, 140),"xp": 150},
]

# Мировой босс (для будущих групповых рейдов, задел на расширение)
WORLD_BOSS = {"name": "Владыка Бездны", "emoji": "👑🐲", "hp": 5000, "atk": 45, "df": 15, "gold": (200, 400), "xp": 500}

SHOP_ITEMS = [
    {"id": "sword_1",   "name": "Ржавый меч",       "emoji": "🗡️", "type": "weapon", "power": 3,  "price": 40},
    {"id": "sword_2",   "name": "Стальной клинок",  "emoji": "⚔️", "type": "weapon", "power": 7,  "price": 150},
    {"id": "sword_3",   "name": "Клинок дракона",   "emoji": "🔱", "type": "weapon", "power": 15, "price": 500},
    {"id": "armor_1",   "name": "Кожаный доспех",   "emoji": "🥋", "type": "armor",  "power": 2,  "price": 35},
    {"id": "armor_2",   "name": "Кольчуга",         "emoji": "🛡️", "type": "armor",  "power": 5,  "price": 140},
    {"id": "armor_3",   "name": "Латы паладина",    "emoji": "🛡️✨", "type": "armor", "power": 12, "price": 480},
    {"id": "potion_s",  "name": "Малое зелье HP",   "emoji": "🧪", "type": "potion", "power": 30, "price": 15},
    {"id": "potion_l",  "name": "Большое зелье HP", "emoji": "⚗️", "type": "potion", "power": 80, "price": 45},
]

LOOT_TABLE = ["Кусок золота", "Старая монета", "Кожа волка", "Клык гоблина", "Магический кристалл"]

def xp_to_next_level(level: int) -> int:
    return int(30 * (level ** 1.5)) + 50
