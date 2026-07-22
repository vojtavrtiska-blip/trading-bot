import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Načtení přihlašovacích údajů z bezpečného prostředí Renderu
EMAIL = os.environ.get("MATCHTRADER_EMAIL")
ACCOUNT_ID = os.environ.get("MATCHTRADER_ACCOUNT")
PASSWORD = os.environ.get("MATCHTRADER_PASSWORD")
SERVER = os.environ.get("MATCHTRADER_SERVER", "FundingPips")

# API URL pro MatchTrader (Funding Pips)
BASE_URL = "https://gtrader.fundingpips.com/api"

# Převodní slovník symbolů
SYMBOL_MAP = {
    "TVC:NDQ": "NAS100",
    "NDQ": "NAS100",
    "US100": "NAS100"
}

def get_auth_token():
    """Získá přihlašovací token z MatchTrader API"""
    try:
        url = f"{BASE_URL}/auth/login"
        payload = {
            "email": EMAIL,
            "password": PASSWORD,
            "server": SERVER
        }
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            return res.json().get("token")
        else:
            print(f"❌ Chyba přihlášení do MatchTraderu: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        print(f"❌ Výjimka při autentičnosti: {e}")
        return None

def open_matchtrader_position(action, symbol, price):
    """Otevírá pozici v MatchTraderu"""
    token = get_auth_token()
    if not token:
        print("❌ Nelze otevřít obchod - chybí přístupový token.")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Určení směru obchodu (BUY = 0/BUY, SELL = 1/SELL podle MatchTrader specifikace)
    cmd = "BUY" if action == "BUY" else "SELL"

    # Základní objem pro $5K účet (např. 0.10 lotu pro NAS100)
    volume = 0.10 

    payload = {
        "account": ACCOUNT_ID,
        "symbol": symbol,
        "cmd": cmd,
        "volume": volume
    }

    try:
        url = f"{BASE_URL}/trade/open"
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            print(f"✅ OBCHOD ÚSPĚŠNĚ OTEVŘEN NA MATCHTRADERU: {cmd} {symbol} (Volume: {volume})")
            return True
        else:
            print(f"❌ MatchTrader zamítl příkaz: {res.status_code} - {res.text}")
            return False
    except Exception as e:
        print(f"❌ Výjimka při otevírání obchodu: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        raw_data = request.get_data(as_text=True)
        
        try:
            data = json.loads(raw_data)
        except Exception:
            data = request.form.to_dict() if request.form else {}

        raw_symbol = data.get("symbol", "")
        action = str(data.get("action", "")).upper()
        price = data.get("price", 0)

        trade_symbol = SYMBOL_MAP.get(raw_symbol, raw_symbol)

        print(f"📥 PŘIJAT SIGNÁL Z TRADINGVIEW: {action} {trade_symbol} @ {price}")

        # Spuštění exekuce obchodu
        if action in ["BUY", "SELL"]:
            open_matchtrader_position(action, trade_symbol, price)

        return jsonify({
            "status": "success",
            "executed_symbol": trade_symbol,
            "action": action
        }), 200

    except Exception as e:
        print(f"❌ Chyba webhooku: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
