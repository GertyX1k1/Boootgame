from datetime import datetime, timezone, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command

import db
import keyboards as kb
from game_data import RACES, CLASSES, SHOP_ITEMS, xp_to_next_level
from config import IMG_WELCOME

router = Router()


class Reg(StatesGroup):
    choosing_race = State()
    choosing_class = State()


class GuildFSM(StatesGroup):
    creating = State()
    joining = State()


WELCOME = (
    "🏔️ <b>Добро пожаловать в Аркхейм!</b>\n\n"
    "Мир магии, чудовищ и древних тайн ждёт своего героя.\n"
    "Сразись с монстрами, добудь легендарное снаряжение, вступи в гильдию "
    "и стань величайшим воином королевства!\n\n"
    "Выбери свою расу, чтобы начать путь:"
)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if user:
        if user["banned"]:
            await message.answer("🚫 Вы заблокированы в этой игре.")
            return
        await message.answer(
            f"👋 С возвращением, <b>{user['name']}</b>!\nЧто будем делать?",
            reply_markup=kb.main_menu()
        )
        return
    await state.set_state(Reg.choosing_race)
    if IMG_WELCOME:
        await message.answer_photo(IMG_WELCOME, caption=WELCOME, reply_markup=kb.race_menu())
    else:
        await message.answer(WELCOME, reply_markup=kb.race_menu())


@router.callback_query(Reg.choosing_race, F.data.startswith("race_"))
async def choose_race(call: CallbackQuery, state: FSMContext):
    race_key = call.data.split("_", 1)[1]
    await state.update_data(race=race_key)
    await state.set_state(Reg.choosing_class)
    await call.message.edit_text(
        f"Раса выбрана: {RACES[race_key]['name']}\n\nТеперь выбери класс героя:",
        reply_markup=kb.class_menu()
    )
    await call.answer()


@router.callback_query(Reg.choosing_class, F.data.startswith("class_"))
async def choose_class(call: CallbackQuery, state: FSMContext):
    class_key = call.data.split("_", 1)[1]
    data = await state.get_data()
    race_key = data["race"]
    race = RACES[race_key]
    cls = CLASSES[class_key]

    hp = 20 + race["hp"] + cls["hp"]
    atk = 3 + race["atk"] + cls["atk"]
    df = 1 + race["df"] + cls["df"]

    name = call.from_user.first_name or "Герой"
    db.create_user(call.from_user.id, call.from_user.username or "", name, race_key, class_key, hp, atk, df)
    await state.clear()

    text = (
        f"🎉 <b>Персонаж создан!</b>\n\n"
        f"{race['name']} — {cls['name']}\n"
        f"❤️ HP: {hp}  ⚔️ Атака: {atk}  🛡️ Защита: {df}\n"
        f"Особая способность: <i>{cls['skill']}</i>\n\n"
        f"Начни свой путь командой /explore или через меню ниже 👇"
    )
    await call.message.edit_text(text, reply_markup=kb.main_menu())
    await call.answer("Добро пожаловать в Аркхейм! 🗡️")


@router.message(Command("menu"))
@router.callback_query(F.data == "menu")
async def show_menu(event):
    text = "🗺️ <b>Главное меню</b>\nВыбери действие:"
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb.main_menu())
    else:
        await event.message.edit_text(text, reply_markup=kb.main_menu())
        await event.answer()


def format_profile(user: dict) -> str:
    need_xp = xp_to_next_level(user["level"])
    bar_len = 10
    filled = int(bar_len * user["xp"] / need_xp) if need_xp else 0
    bar = "▰" * filled + "▱" * (bar_len - filled)
    race_name = RACES.get(user["race"], {}).get("name", user["race"])
    class_name = CLASSES.get(user["class"], {}).get("name", user["class"])
    return (
        f"👤 <b>{user['name']}</b>\n"
        f"{race_name} · {class_name} · Уровень {user['level']}\n\n"
        f"❤️ HP: {user['hp']}/{user['max_hp']}\n"
        f"⚔️ Атака: {user['atk']}   🛡️ Защита: {user['df']}\n"
        f"✨ Опыт: {user['xp']}/{need_xp}\n{bar}\n\n"
        f"💰 Золото: {user['gold']}   💎 Кристаллы: {user['gems']}\n"
        f"🏆 Победы: {user['wins']}   💀 Поражения: {user['losses']}"
    )


@router.message(Command("profile"))
@router.callback_query(F.data == "profile")
async def profile(event):
    uid = event.from_user.id
    user = db.get_user(uid)
    if not user:
        text = "Сначала начни игру: /start"
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.answer(text, show_alert=True)
        return
    text = format_profile(user)
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb.back_menu())
    else:
        await event.message.edit_text(text, reply_markup=kb.back_menu())
        await event.answer()


@router.message(Command("inventory"))
@router.callback_query(F.data == "inventory")
async def inventory(event):
    uid = event.from_user.id
    items = db.get_inventory(uid)
    if not items:
        text = "🎒 Твой инвентарь пуст. Загляни в 🏪 магазин!"
    else:
        text = "🎒 <b>Инвентарь</b>\nНажми на предмет, чтобы экипировать/использовать:"
    markup = kb.inventory_menu(items) if items else kb.back_menu()
    if isinstance(event, Message):
        await event.answer(text, reply_markup=markup)
    else:
        await event.message.edit_text(text, reply_markup=markup)
        await event.answer()


@router.callback_query(F.data.startswith("item_"))
async def use_item(call: CallbackQuery):
    inv_id = int(call.data.split("_", 1)[1])
    items = {i["id"]: i for i in db.get_inventory(call.from_user.id)}
    item = items.get(inv_id)
    if not item:
        await call.answer("Предмет не найден", show_alert=True)
        return
    user = db.get_user(call.from_user.id)

    if item["item_type"] == "potion":
        heal = min(item["power"], user["max_hp"] - user["hp"])
        db.update_user(user["user_id"], hp=user["hp"] + heal)
        db.consume_potion(inv_id)
        await call.answer(f"Выпито! +{heal} HP ❤️", show_alert=True)
    else:
        db.equip_item(user["user_id"], inv_id, item["item_type"])
        if item["item_type"] == "weapon":
            db.update_user(user["user_id"], atk=user["atk"])  # атака считается динамически при бою
        await call.answer(f"Экипировано: {item['item_name']} ✅", show_alert=True)

    items = db.get_inventory(call.from_user.id)
    await call.message.edit_text("🎒 <b>Инвентарь</b>\nНажми на предмет, чтобы экипировать/использовать:",
                                  reply_markup=kb.inventory_menu(items) if items else kb.back_menu())


def equipped_bonus(user_id: int):
    """Возвращает (atk_bonus, def_bonus) от экипированных предметов."""
    atk_b, df_b = 0, 0
    for it in db.get_inventory(user_id):
        if it["equipped"] and it["item_type"] == "weapon":
            atk_b += it["power"]
        if it["equipped"] and it["item_type"] == "armor":
            df_b += it["power"]
    return atk_b, df_b


@router.message(Command("shop"))
@router.callback_query(F.data == "shop")
async def shop(event):
    text = "🏪 <b>Лавка торговца</b>\nЧто желаешь приобрести?"
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb.shop_menu())
    else:
        await event.message.edit_text(text, reply_markup=kb.shop_menu())
        await event.answer()


@router.callback_query(F.data.startswith("buy_"))
async def buy_item(call: CallbackQuery):
    item_id = call.data.split("_", 1)[1]
    item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
    if not item:
        await call.answer("Товар не найден", show_alert=True)
        return
    user = db.get_user(call.from_user.id)
    if user["gold"] < item["price"]:
        await call.answer("Недостаточно золота! 💰", show_alert=True)
        return
    db.update_user(user["user_id"], gold=user["gold"] - item["price"])
    db.add_item(user["user_id"], item["id"], item["name"], item["type"], item["power"])
    await call.answer(f"Куплено: {item['name']} {item['emoji']}", show_alert=True)


@router.message(Command("daily"))
@router.callback_query(F.data == "daily")
async def daily(event):
    uid = event.from_user.id
    user = db.get_user(uid)
    if not user:
        return
    now = datetime.now(timezone.utc)
    if user["last_daily"]:
        last = datetime.fromisoformat(user["last_daily"])
        if now - last < timedelta(hours=20):
            remaining = timedelta(hours=20) - (now - last)
            h = remaining.seconds // 3600
            text = f"⏳ Награда уже получена. Приходи через ~{h} ч."
            if isinstance(event, Message):
                await event.answer(text)
            else:
                await event.answer(text, show_alert=True)
            return
    gold_reward = 30 + user["level"] * 5
    db.update_user(uid, gold=user["gold"] + gold_reward, last_daily=now.isoformat())
    text = f"🎁 <b>Ежедневная награда получена!</b>\n💰 +{gold_reward} золота"
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb.back_menu())
    else:
        await event.answer(f"+{gold_reward} золота 💰", show_alert=True)


@router.message(Command("top"))
@router.callback_query(F.data == "top")
async def top(event):
    players = db.get_top(10)
    if not players:
        text = "Пока никто не начал игру."
    else:
        lines = ["🏆 <b>Топ героев Аркхейма</b>\n"]
        medals = ["🥇", "🥈", "🥉"]
        for i, p in enumerate(players):
            medal = medals[i] if i < 3 else f"{i+1}."
            lines.append(f"{medal} {p['name']} — ур.{p['level']} ({p['wins']} побед)")
        text = "\n".join(lines)
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb.back_menu())
    else:
        await event.message.edit_text(text, reply_markup=kb.back_menu())
        await event.answer()


@router.message(Command("help"))
async def help_cmd(message: Message):
    text = (
        "📖 <b>Команды Аркхейма</b>\n\n"
        "/start — начать игру\n"
        "/profile — профиль героя\n"
        "/explore — исследовать мир и сражаться\n"
        "/inventory — инвентарь и снаряжение\n"
        "/shop — магазин\n"
        "/daily — ежедневная награда\n"
        "/pvp @username — вызов на дуэль\n"
        "/guild — гильдии\n"
        "/top — таблица лидеров\n"
        "/menu — главное меню"
    )
    await message.answer(text)


# ---------- ГИЛЬДИИ ----------

@router.message(Command("guild"))
@router.callback_query(F.data == "guild")
async def guild(event):
    uid = event.from_user.id
    user = db.get_user(uid)
    if not user:
        return
    if user["guild_id"]:
        g = db.get_guild(user["guild_id"])
        text = f"🏰 <b>{g['name']}</b>\nУровень гильдии: {g['level']}\nКазна: {g['gold']}💰"
    else:
        text = "🏰 Ты пока не состоишь в гильдии. Создай свою или вступи в существующую!"
    markup = kb.guild_menu(bool(user["guild_id"]))
    if isinstance(event, Message):
        await event.answer(text, reply_markup=markup)
    else:
        await event.message.edit_text(text, reply_markup=markup)
        await event.answer()


@router.callback_query(F.data == "guild_create")
async def guild_create_prompt(call: CallbackQuery, state: FSMContext):
    await state.set_state(GuildFSM.creating)
    await call.message.edit_text("✏️ Отправь название новой гильдии (одним сообщением):")
    await call.answer()


@router.message(GuildFSM.creating)
async def guild_create_do(message: Message, state: FSMContext):
    name = message.text.strip()[:32]
    if db.get_guild_by_name(name):
        await message.answer("Такое название уже занято, попробуй другое.")
        return
    guild_id = db.create_guild(name, message.from_user.id)
    db.update_user(message.from_user.id, guild_id=guild_id)
    await state.clear()
    await message.answer(f"🏰 Гильдия <b>{name}</b> создана! Ты — глава гильдии.", reply_markup=kb.main_menu())


@router.callback_query(F.data == "guild_join")
async def guild_join_prompt(call: CallbackQuery, state: FSMContext):
    await state.set_state(GuildFSM.joining)
    await call.message.edit_text("✏️ Отправь точное название гильдии, к которой хочешь присоединиться:")
    await call.answer()


@router.message(GuildFSM.joining)
async def guild_join_do(message: Message, state: FSMContext):
    g = db.get_guild_by_name(message.text.strip())
    if not g:
        await message.answer("Гильдия не найдена. Проверь название и попробуй снова.")
        return
    db.update_user(message.from_user.id, guild_id=g["guild_id"])
    await state.clear()
    await message.answer(f"🎉 Ты вступил в гильдию <b>{g['name']}</b>!", reply_markup=kb.main_menu())


@router.callback_query(F.data == "guild_leave")
async def guild_leave(call: CallbackQuery):
    db.update_user(call.from_user.id, guild_id=None)
    await call.message.edit_text("🚪 Ты покинул гильдию.", reply_markup=kb.main_menu())
    await call.answer()


@router.callback_query(F.data == "guild_members")
async def guild_members_view(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    members = db.guild_members(user["guild_id"])
    lines = [f"👥 <b>Участники гильдии</b>\n"]
    for m in members:
        lines.append(f"• {m['name']} — ур.{m['level']}")
    await call.message.edit_text("\n".join(lines), reply_markup=kb.back_menu())
    await call.answer()


@router.callback_query(F.data == "guild_top")
async def guild_top_view(call: CallbackQuery):
    guilds = db.top_guilds(10)
    lines = ["🏆 <b>Топ гильдий</b>\n"]
    for i, g in enumerate(guilds, 1):
        lines.append(f"{i}. {g['name']} — {g['members']} чел., мощь {g['power']}")
    await call.message.edit_text("\n".join(lines), reply_markup=kb.back_menu())
    await call.answer()
