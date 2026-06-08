from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from data.texts import *
from data.keyboards import *
from database.models import get_stats, get_transactions, get_users_list, ban_user, db
import os

router = Router()
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "872151895,6593438966").split(",")]

def is_admin(uid): return uid in ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id): return
    s = get_stats()
    await message.answer(
        ADMIN_TEXT.format(users=s['users'], transactions=s['transactions'], revenue=s['revenue']),
        reply_markup=admin_keyboard()
    )

@router.callback_query(F.data == "admin")
async def admin_back(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    s = get_stats()
    await call.message.edit_text(
        ADMIN_TEXT.format(users=s['users'], transactions=s['transactions'], revenue=s['revenue']),
        reply_markup=admin_keyboard()
    )
    await call.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    s = get_stats()
    await call.message.edit_text(
        f"📊 <b>СТАТИСТИКА:</b>\n\n👥 Юзеров: {s['users']}\n💰 Транзакций: {s['transactions']}\n💵 Доход: {s['revenue']}₽",
        reply_markup=back_admin()
    )
    await call.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    users = get_users_list(30)
    text = "👥 <b>ПОСЛЕДНИЕ 30 ЮЗЕРОВ:</b>\n\n"
    for u in users:
        ban = "🚫" if u.get('banned') else "✅"
        text += f"{ban} <code>{u['user_id']}</code> @{u.get('username','?')}\n"
    await call.message.edit_text(text, reply_markup=back_admin())
    await call.answer()

@router.callback_query(F.data == "admin_trans")
async def admin_trans(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    trans = get_transactions(30)
    if not trans: await call.message.edit_text("Нет транзакций.", reply_markup=back_admin()); return
    text = "💰 <b>ТРАНЗАКЦИИ:</b>\n\n"
    for t in trans:
        text += f"#{t['id']} | <code>{t['user_id']}</code> | {t['type']} | {t['amount']} {t['currency']} | {t['created_at'][:16]}\n"
    await call.message.edit_text(text, reply_markup=back_admin())
    await call.answer()

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    await call.message.edit_text("📢 <b>РАССЫЛКА</b>\n\n<code>/bc ТЕКСТ</code>", reply_markup=back_admin())
    await call.answer()

@router.message(Command("bc"))
async def broadcast(message: Message):
    if not is_admin(message.from_user.id): return
    text = message.text.replace("/bc ", "", 1)
    if text == "/bc": return
    users = db.fetchall("SELECT user_id FROM users WHERE banned=0")
    sent = 0
    for u in users:
        try: await message.bot.send_message(u['user_id'], f"📢 {text}"); sent += 1
        except: pass
    await message.answer(f"✅ Отправлено: {sent}/{len(users)}")

@router.message(Command("unban"))
async def unban_user(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2: return
    uid = int(args[1])
    db.update('users', {'banned': 0}, 'user_id=?', (uid,))
    await message.answer(f"✅ {uid} разбанен!")

@router.callback_query(F.data == "close")
async def close(call: CallbackQuery): await call.message.delete(); await call.answer()