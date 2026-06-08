from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.texts import SUPPORT_URL

def start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 КУПИТЬ КРИПТУ", callback_data="buy_crypto")
    builder.button(text="💎 ПРОДАТЬ КРИПТУ", callback_data="sell_crypto")
    builder.button(text="📊 КУРСЫ", callback_data="rates")
    builder.button(text="📞 ПОДДЕРЖКА", url=SUPPORT_URL)
    builder.adjust(1)
    return builder.as_markup()

def buy_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="₿ CRYPTOBOT", callback_data="buy_crypto_bot")
    builder.button(text="💳 КАРТА", callback_data="buy_card")
    builder.button(text="◀️ НАЗАД", callback_data="start")
    builder.adjust(2, 1)
    return builder.as_markup()

def sell_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Я ОТПРАВИЛ", callback_data="sent_crypto")
    builder.button(text="◀️ НАЗАД", callback_data="start")
    builder.adjust(1)
    return builder.as_markup()

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 СТАТИСТИКА", callback_data="admin_stats")
    builder.button(text="👥 ЮЗЕРЫ", callback_data="admin_users")
    builder.button(text="💰 ТРАНЗАКЦИИ", callback_data="admin_trans")
    builder.button(text="📢 РАССЫЛКА", callback_data="admin_broadcast")
    builder.button(text="❌ ЗАКРЫТЬ", callback_data="close")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def back_admin():
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ НАЗАД", callback_data="admin")
    return builder.as_markup()