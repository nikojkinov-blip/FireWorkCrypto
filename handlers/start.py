from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.texts import *
from data.keyboards import *
from database.models import get_user, create_user, is_banned

router = Router()

@router.message(Command("start"))
async def start(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    if is_banned(message.from_user.id):
        await message.answer("🚫 Вы заблокированы.")
        return
    
    await message.answer(
        START_TEXT,
        reply_markup=start_keyboard()
    )

@router.callback_query(F.data == "start")
async def back_start(call: CallbackQuery):
    await call.message.edit_text(START_TEXT, reply_markup=start_keyboard())
    await call.answer()

@router.callback_query(F.data == "rates")
async def rates(call: CallbackQuery):
    await call.message.edit_text(
        "📊 <b>КУРСЫ ВАЛЮТ:</b>\n\n"
        "💰 <b>Покупка USDT:</b> 75₽\n"
        "💎 <b>Продажа USDT:</b> 70₽\n\n"
        "⚡ Лучший курс на рынке!\n"
        "🔐 Без верификации",
        reply_markup=InlineKeyboardBuilder().button(text="◀️ НАЗАД", callback_data="start").as_markup()
    )
    await call.answer()
