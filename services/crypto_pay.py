import aiohttp
import os

TOKEN = os.getenv("CRYPTO_BOT_TOKEN", "")
API = "https://pay.crypt.bot/api"

class CryptoPay:
    @staticmethod
    async def create_invoice(amount_rub: float, currency: str = "USDT") -> dict:
        headers = {"Crypto-Pay-API-Token": TOKEN, "Content-Type": "application/json"}
        rates = {"TON": 150, "USDT": 90, "BTC": 6000000}
        crypto_amount = round(amount_rub / rates.get(currency, 90), 2)
        data = {"asset": currency, "amount": str(crypto_amount), "description": "CryptoFireWork Exchange", "payload": "exchange", "expires_in": 1800}
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{API}/createInvoice", headers=headers, json=data) as r:
                res = await r.json()
                if res.get("ok"):
                    inv = res["result"]
                    return {"invoice_id": inv["invoice_id"], "pay_url": inv["pay_url"], "amount": inv["amount"], "asset": inv["asset"]}
        return None

    @staticmethod
    async def check_invoice(inv_id: int) -> str:
        headers = {"Crypto-Pay-API-Token": TOKEN, "Content-Type": "application/json"}
        data = {"invoice_ids": [inv_id]}
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{API}/getInvoices", headers=headers, json=data) as r:
                res = await r.json()
                if res.get("ok") and res["result"]["items"]:
                    return res["result"]["items"][0]["status"]
        return "unknown"