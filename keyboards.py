from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from game_data import RACES, CLASSES, SHOP_ITEMS


def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="⚔️ Исследовать", callback_data="explore")
    kb.button(text="👤 Профиль", callback_data="profile")
    kb.button(text="🎒 Инвентарь", callback_data="inventory")
    kb.button(text="🏪 Магазин", callback_data="shop")
    kb.button(text="🏰 Гильдия", callback_data="guild")
    kb.button(text="⚔️ Дуэль (PvP)", callback_data="pvp")
    kb.button(text="🎁 Ежедневная награда", callback_data="daily")
    kb.button(text="🏆 Топ игроков", callback_data="top")
    kb.adjust(2, 2, 2, 2)
    return kb.as_markup()


def race_menu():
    kb = InlineKeyboardBuilder()
    for key, r in RACES.items():
        kb.button(text=r["name"], callback_data=f"race_{key}")
    kb.adjust(2)
    return kb.as_markup()


def class_menu():
    kb = InlineKeyboardBuilder()
    for key, c in CLASSES.items():
        kb.button(text=c["name"], callback_data=f"class_{key}")
    kb.adjust(2)
    return kb.as_markup()


def battle_menu(has_potion=True):
    kb = InlineKeyboardBuilder()
    kb.button(text="🗡️ Атаковать", callback_data="battle_attack")
    kb.button(text="✨ Способность", callback_data="battle_skill")
    if has_potion:
        kb.button(text="🧪 Зелье", callback_data="battle_potion")
    kb.button(text="🏃 Сбежать", callback_data="battle_flee")
    kb.adjust(2, 2)
    return kb.as_markup()


def shop_menu():
    kb = InlineKeyboardBuilder()
    for item in SHOP_ITEMS:
        kb.button(text=f"{item['emoji']} {item['name']} — {item['price']}💰", callback_data=f"buy_{item['id']}")
    kb.button(text="⬅️ Назад", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def inventory_menu(items):
    kb = InlineKeyboardBuilder()
    for it in items:
        mark = "✅ " if it["equipped"] else ""
        label = f"{mark}{it['item_name']}"
        if it["item_type"] == "potion":
            label += f" x{it['qty']}"
        kb.button(text=label, callback_data=f"item_{it['id']}")
    kb.button(text="⬅️ Назад", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def back_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В меню", callback_data="menu")
    return kb.as_markup()


def guild_menu(in_guild: bool):
    kb = InlineKeyboardBuilder()
    if in_guild:
        kb.button(text="👥 Участники", callback_data="guild_members")
        kb.button(text="🚪 Покинуть гильдию", callback_data="guild_leave")
    else:
        kb.button(text="➕ Создать гильдию", callback_data="guild_create")
        kb.button(text="🔎 Вступить в гильдию", callback_data="guild_join")
    kb.button(text="🏆 Топ гильдий", callback_data="guild_top")
    kb.button(text="⬅️ Назад", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Статистика", callback_data="adm_stats")
    kb.button(text="📢 Рассылка", callback_data="adm_broadcast")
    kb.button(text="🎁 Выдать награду", callback_data="adm_give")
    kb.button(text="🚫 Забанить", callback_data="adm_ban")
    kb.button(text="✅ Разбанить", callback_data="adm_unban")
    kb.button(text="🔍 Профиль игрока", callback_data="adm_lookup")
    kb.adjust(2, 2, 2)
    return kb.as_markup()


def confirm_menu(yes_cb: str, no_cb: str = "menu"):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data=yes_cb)
    kb.button(text="❌ Отмена", callback_data=no_cb)
    kb.adjust(2)
    return kb.as_markup()
