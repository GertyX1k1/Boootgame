import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

import db
import keyboards as kb
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AdminFSM(StatesGroup):
    broadcast_text = State()
    give_target = State()
    give_amount = State()
    ban_target = State()
    unban_target = State()
    lookup_target = State()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠️ <b>Панель администратора</b>\nВыбери действие:", reply_markup=kb.admin_menu())


@router.callback_query(F.data == "adm_stats")
async def adm_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer()
    s = db.stats()
    text = (
        f"📊 <b>Статистика игры</b>\n\n"
        f"👥 Всего игроков: {s['total']}\n"
        f"🚫 Забанено: {s['banned']}\n"
        f"🌟 Макс. уровень: {s['top_level']}\n"
        f"💰 Золота у всех игроков: {s['total_gold']}"
    )
    await call.message.edit_text(text, reply_markup=kb.admin_menu())
    await call.answer()


@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminFSM.broadcast_text)
    await call.message.edit_text("✏️ Отправь текст рассылки для всех игроков (поддерживается HTML-разметка):")
    await call.answer()


@router.message(AdminFSM.broadcast_text)
async def adm_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    ids = db.all_user_ids()
    sent, failed = 0, 0
    status = await message.answer(f"📢 Начинаю рассылку на {len(ids)} игроков...")
    for uid in ids:
        try:
            await bot.send_message(uid, f"📢 <b>Объявление</b>\n\n{message.html_text}")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await status.edit_text(f"✅ Рассылка завершена.\nДоставлено: {sent}\nОшибок: {failed}")


@router.callback_query(F.data == "adm_give")
async def adm_give_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminFSM.give_target)
    await call.message.edit_text("✏️ Отправь ID игрока, которому хочешь выдать золото:")
    await call.answer()


@router.message(AdminFSM.give_target)
async def adm_give_target(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("Некорректный ID. Отправь число.")
        return
    if not db.get_user(target_id):
        await message.answer("Игрок с таким ID не найден.")
        return
    await state.update_data(target_id=target_id)
    await state.set_state(AdminFSM.give_amount)
    await message.answer("💰 Сколько золота выдать? (можно отрицательное число, чтобы забрать)")


@router.message(AdminFSM.give_amount)
async def adm_give_amount(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("Отправь целое число.")
        return
    data = await state.get_data()
    target_id = data["target_id"]
    user = db.get_user(target_id)
    new_gold = max(0, user["gold"] + amount)
    db.update_user(target_id, gold=new_gold)
    await state.clear()
    await message.answer(f"✅ Игроку {user['name']} выдано {amount} золота. Новый баланс: {new_gold}💰")
    try:
        await bot.send_message(target_id, f"🎁 Администратор изменил твой баланс: {amount:+d} золота.")
    except Exception:
        pass


@router.callback_query(F.data == "adm_ban")
async def adm_ban_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminFSM.ban_target)
    await call.message.edit_text("✏️ Отправь ID игрока для бана:")
    await call.answer()


@router.message(AdminFSM.ban_target)
async def adm_ban_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("Некорректный ID.")
        return
    if not db.get_user(target_id):
        await message.answer("Игрок не найден.")
        return
    db.update_user(target_id, banned=1)
    await state.clear()
    await message.answer(f"🚫 Игрок {target_id} забанен.")


@router.callback_query(F.data == "adm_unban")
async def adm_unban_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminFSM.unban_target)
    await call.message.edit_text("✏️ Отправь ID игрока для разбана:")
    await call.answer()


@router.message(AdminFSM.unban_target)
async def adm_unban_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("Некорректный ID.")
        return
    if not db.get_user(target_id):
        await message.answer("Игрок не найден.")
        return
    db.update_user(target_id, banned=0)
    await state.clear()
    await message.answer(f"✅ Игрок {target_id} разбанен.")


@router.callback_query(F.data == "adm_lookup")
async def adm_lookup_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer()
    await state.set_state(AdminFSM.lookup_target)
    await call.message.edit_text("✏️ Отправь ID игрока, чтобы посмотреть его профиль:")
    await call.answer()


@router.message(AdminFSM.lookup_target)
async def adm_lookup_do(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("Некорректный ID.")
        return
    user = db.get_user(target_id)
    await state.clear()
    if not user:
        await message.answer("Игрок не найден.")
        return
    text = (
        f"🔍 <b>{user['name']}</b> (ID {user['user_id']})\n"
        f"Уровень {user['level']} · {user['class']}\n"
        f"HP {user['hp']}/{user['max_hp']} · ATK {user['atk']} · DEF {user['df']}\n"
        f"💰 {user['gold']}   💎 {user['gems']}\n"
        f"🏆 {user['wins']}П / {user['losses']}П\n"
        f"Забанен: {'да 🚫' if user['banned'] else 'нет ✅'}"
    )
    await message.answer(text, reply_markup=kb.admin_menu())
