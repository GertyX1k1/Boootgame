import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

import db
import keyboards as kb
from game_data import MONSTERS, LOOT_TABLE, xp_to_next_level
from handlers.user import equipped_bonus, format_profile
from config import IMG_BATTLE, IMG_VICTORY, IMG_DEFEAT, IMG_LEVELUP

router = Router()

# Битвы держим в памяти процесса: user_id -> battle dict
ACTIVE_BATTLES: dict[int, dict] = {}
PVP_CHALLENGES: dict[int, int] = {}  # challenger_id -> target_id


def pick_monster(level: int):
    candidates = [m for m in MONSTERS if m["min_lvl"] <= level] or [MONSTERS[0]]
    # чем выше уровень героя, тем больше шанс сильных монстров из доступного пула
    weights = [i + 1 for i in range(len(candidates))]
    return random.choices(candidates, weights=weights, k=1)[0]


def monster_hp_bar(hp, max_hp, length=10):
    filled = max(0, int(length * hp / max_hp))
    return "🟥" * filled + "⬛" * (length - filled)


async def start_explore(uid: int, message_or_call):
    user = db.get_user(uid)
    if not user:
        return
    if user["hp"] <= 0:
        text = "💀 Ты слишком слаб для похода. Используй зелье или подожди восстановления."
        if isinstance(message_or_call, CallbackQuery):
            await message_or_call.answer(text, show_alert=True)
        else:
            await message_or_call.answer(text)
        return

    roll = random.random()
    if roll < 0.15:
        # мирное событие — находка
        loot = random.choice(LOOT_TABLE)
        gold = random.randint(3, 10)
        db.update_user(uid, gold=user["gold"] + gold)
        text = f"🌲 Ты прошёл через тихую поляну и нашёл: <b>{loot}</b> и 💰{gold} золота."
        markup = kb.back_menu()
        if isinstance(message_or_call, CallbackQuery):
            await message_or_call.message.edit_text(text, reply_markup=markup)
            await message_or_call.answer()
        else:
            await message_or_call.answer(text, reply_markup=markup)
        return

    monster = pick_monster(user["level"])
    m_hp = monster["hp"] + (user["level"] - monster["min_lvl"]) * 2
    ACTIVE_BATTLES[uid] = {"monster": dict(monster), "m_hp": m_hp, "m_max_hp": m_hp, "type": "pve"}

    text = (
        f"⚔️ <b>Встреча!</b>\n\n"
        f"{monster['emoji']} <b>{monster['name']}</b> преграждает тебе путь!\n"
        f"{monster_hp_bar(m_hp, m_hp)}  {m_hp}/{m_hp} HP\n\n"
        f"Твоё HP: {user['hp']}/{user['max_hp']} ❤️"
    )
    if isinstance(message_or_call, CallbackQuery):
        await message_or_call.message.edit_text(text, reply_markup=kb.battle_menu())
        await message_or_call.answer()
    else:
        await message_or_call.answer(text, reply_markup=kb.battle_menu())


@router.message(Command("explore"))
async def explore_cmd(message: Message):
    await start_explore(message.from_user.id, message)


@router.callback_query(F.data == "explore")
async def explore_cb(call: CallbackQuery):
    await start_explore(call.from_user.id, call)


def has_potion(uid: int) -> bool:
    return any(i["item_type"] == "potion" for i in db.get_inventory(uid))


async def end_battle_win(uid: int, call: CallbackQuery, battle: dict):
    user = db.get_user(uid)
    monster = battle["monster"]
    gold = random.randint(*monster["gold"])
    xp_gain = monster["xp"]
    new_xp = user["xp"] + xp_gain
    new_level = user["level"]
    leveled_up = False
    need = xp_to_next_level(new_level)
    while new_xp >= need:
        new_xp -= need
        new_level += 1
        leveled_up = True
        need = xp_to_next_level(new_level)

    updates = {"gold": user["gold"] + gold, "xp": new_xp, "wins": user["wins"] + 1}
    if leveled_up:
        new_max_hp = user["max_hp"] + 15
        updates.update(level=new_level, max_hp=new_max_hp, hp=new_max_hp,
                        atk=user["atk"] + 3, df=user["df"] + 2)
    db.update_user(uid, **updates)
    del ACTIVE_BATTLES[uid]

    text = (
        f"🏆 <b>Победа!</b>\n\n"
        f"Ты повергнул {monster['emoji']} {monster['name']}!\n"
        f"💰 +{gold} золота   ✨ +{xp_gain} опыта"
    )
    if leveled_up:
        text += f"\n\n🌟 <b>Новый уровень: {new_level}!</b> Характеристики выросли!"
    await call.message.edit_text(text, reply_markup=kb.back_menu())
    await call.answer()


async def end_battle_lose(uid: int, call: CallbackQuery):
    user = db.get_user(uid)
    db.update_user(uid, hp=1, losses=user["losses"] + 1)
    del ACTIVE_BATTLES[uid]
    text = "💀 <b>Поражение...</b>\nТы едва выжил и отступил зализывать раны. Восстанови HP зельем или подожди."
    await call.message.edit_text(text, reply_markup=kb.back_menu())
    await call.answer()


@router.callback_query(F.data.startswith("battle_"))
async def battle_action(call: CallbackQuery):
    uid = call.from_user.id
    battle = ACTIVE_BATTLES.get(uid)
    if not battle:
        await call.answer("Бой уже завершён.", show_alert=True)
        return
    action = call.data.split("_", 1)[1]
    user = db.get_user(uid)
    atk_bonus, df_bonus = equipped_bonus(uid)
    my_atk = user["atk"] + atk_bonus
    my_df = user["df"] + df_bonus
    monster = battle["monster"]
    log = []

    if action == "flee":
        chance = random.random()
        if chance < 0.5:
            del ACTIVE_BATTLES[uid]
            await call.message.edit_text("🏃 Ты успешно сбежал от боя.", reply_markup=kb.back_menu())
            await call.answer()
            return
        else:
            log.append("🏃 Побег не удался!")

    elif action == "attack":
        dmg = max(1, my_atk - monster["df"] // 2 + random.randint(-2, 3))
        battle["m_hp"] -= dmg
        log.append(f"🗡️ Ты бьёшь и наносишь {dmg} урона.")

    elif action == "skill":
        dmg = max(1, int((my_atk * 1.6)) - monster["df"] // 3 + random.randint(-1, 4))
        battle["m_hp"] -= dmg
        log.append(f"✨ Способность! {dmg} урона монстру.")

    elif action == "potion":
        potions = [i for i in db.get_inventory(uid) if i["item_type"] == "potion"]
        if not potions:
            await call.answer("Нет зелий!", show_alert=True)
            return
        p = potions[0]
        heal = min(p["power"], user["max_hp"] - user["hp"])
        db.update_user(uid, hp=user["hp"] + heal)
        db.consume_potion(p["id"])
        user = db.get_user(uid)
        log.append(f"🧪 Выпито зелье, +{heal} HP.")

    # монстр жив — атакует в ответ
    if battle["m_hp"] > 0:
        m_dmg = max(1, monster["atk"] - my_df // 2 + random.randint(-2, 3))
        new_hp = user["hp"] - m_dmg
        db.update_user(uid, hp=max(0, new_hp))
        log.append(f"{monster['emoji']} {monster['name']} атакует в ответ: -{m_dmg} HP.")
        user = db.get_user(uid)

    if battle["m_hp"] <= 0:
        await end_battle_win(uid, call, battle)
        return
    if user["hp"] <= 0:
        await end_battle_lose(uid, call)
        return

    text = (
        f"{monster['emoji']} <b>{monster['name']}</b>\n"
        f"{monster_hp_bar(battle['m_hp'], battle['m_max_hp'])}  {max(0,battle['m_hp'])}/{battle['m_max_hp']} HP\n\n"
        f"{chr(10).join(log)}\n\n"
        f"Твоё HP: {user['hp']}/{user['max_hp']} ❤️"
    )
    await call.message.edit_text(text, reply_markup=kb.battle_menu(has_potion(uid)))
    await call.answer()


# ---------- PvP ----------

@router.message(Command("pvp"))
async def pvp_challenge(message: Message):
    if not message.reply_to_message and " " not in message.text:
        await message.answer("Используй: ответь на сообщение игрока командой /pvp, чтобы вызвать его на дуэль.")
        return
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        await message.answer("Ответь на сообщение игрока командой /pvp, чтобы вызвать его на дуэль.")
        return
    challenger = db.get_user(message.from_user.id)
    opponent = db.get_user(target.id)
    if not challenger or not opponent:
        await message.answer("Оба игрока должны сначала начать игру через /start.")
        return
    PVP_CHALLENGES[message.from_user.id] = target.id
    await message.answer(
        f"⚔️ {challenger['name']} вызывает {opponent['name']} на дуэль!\n"
        f"{opponent['name']}, введи /accept чтобы принять бой."
    )


@router.message(Command("accept"))
async def pvp_accept(message: Message):
    uid = message.from_user.id
    challenger_id = None
    for ch, tgt in PVP_CHALLENGES.items():
        if tgt == uid:
            challenger_id = ch
            break
    if not challenger_id:
        await message.answer("У тебя нет активных вызовов на дуэль.")
        return
    del PVP_CHALLENGES[challenger_id]

    a = db.get_user(challenger_id)
    b = db.get_user(uid)
    a_atk_b, a_df_b = equipped_bonus(challenger_id)
    b_atk_b, b_df_b = equipped_bonus(uid)

    a_hp, b_hp = a["hp"], b["hp"]
    a_atk, a_df = a["atk"] + a_atk_b, a["df"] + a_df_b
    b_atk, b_df = b["atk"] + b_atk_b, b["df"] + b_df_b
    rounds = []
    turn = 0
    while a_hp > 0 and b_hp > 0 and turn < 30:
        turn += 1
        dmg_to_b = max(1, a_atk - b_df // 2 + random.randint(-2, 3))
        b_hp -= dmg_to_b
        if b_hp <= 0:
            break
        dmg_to_a = max(1, b_atk - a_df // 2 + random.randint(-2, 3))
        a_hp -= dmg_to_a

    winner, loser = (a, b) if b_hp <= 0 else (b, a)
    winner_id = winner["user_id"]
    loser_id = loser["user_id"]
    gold_prize = 15 + winner["level"] * 2

    db.update_user(winner_id, wins=winner["wins"] + 1, gold=winner["gold"] + gold_prize)
    db.update_user(loser_id, losses=loser["losses"] + 1)

    text = (
        f"⚔️ <b>Дуэль завершена!</b>\n\n"
        f"🏆 Победитель: <b>{winner['name']}</b>\n"
        f"💀 Проигравший: {loser['name']}\n\n"
        f"Приз победителю: 💰{gold_prize} золота"
    )
    await message.answer(text)


@router.callback_query(F.data == "pvp")
async def pvp_info(call: CallbackQuery):
    await call.message.edit_text(
        "⚔️ <b>PvP-дуэли</b>\n\n"
        "Чтобы вызвать игрока на бой:\n"
        "1. Ответь на его сообщение командой /pvp\n"
        "2. Он принимает бой командой /accept\n\n"
        "Исход дуэли решают характеристики и экипировка героев!",
        reply_markup=kb.back_menu()
    )
    await call.answer()
