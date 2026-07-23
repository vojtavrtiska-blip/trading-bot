import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Načtení přihlašovacích údajů z Environment Variables v Renderu
EMAIL = os.environ.get("MATCHTRADER_EMAIL")
ACCOUNT_ID = os.environ.get("MATCHTRADER_ACCOUNT")
PASSWORD = os.environ.get("MATCHTRADER_PASSWORD")
SERVER = os.environ.get("MATCHTRADER_SERVER", "FundingPips")

# API endpoint MatchTraderu u Funding Pips
BASE_URL = "https://matchtrader.fundingpips.com/api"

# Převodník symbolů z TradingView na broker formát
SYMBOL_MAP = {
    "TVC:NDQ": "NAS100",
    "NDQ": "NAS100",
    "US100": "NAS100"
}

def get_auth_token():
    """Přihlásí se do MatchTrader API a získá přístupový token"""
    try:
        url = f"{BASE_URL}/auth/login"
        payload = {
            "email": EMAIL,
            "password": PASSWORD,
            "server": SERVER
        }
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("token"), data
        else:
            return None, f"Chyba {res.status_code}: {res.text}"
    except Exception as e:
        return None, str(e)

def open_matchtrader_position(action, symbol, price):
    """Otevírá pozici v MatchTraderu"""
    token, debug_info = get_auth_token()
    if not token:
        print(f"❌ Nelze otevřít obchod - chyba přihlášení: {debug_info}")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    cmd = "BUY" if "BUY" in action else "SELL"
    volume = 0.10  # Objem pro $5K účet

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
            print(f"✅ OBCHOD ÚSPĚŠNĚ OTEVŘEN: {cmd} {symbol} (Volume: {volume})")
            return True
        else:
            print(f"❌ MatchTrader zamítl příkaz: {res.status_code} - {res.text}")
            return False
    except Exception as e:
        print(f"❌ Výjimka při otevírání obchodu: {e}")
        return False

@app.route('/', methods=['GET'])
def home():
    return "Bot je aktivní a běží na Renderu!", 200

@app.route('/test', methods=['GET'])
def test_connection():
    """Testovací adresa pro rychlé ověření přihlášení k MatchTraderu"""
    token, debug_info = get_auth_token()
    if token:
        return jsonify({
            "status": "SUCCESS ✅",
            "message": f"Uspesne pripojeno k uctu {ACCOUNT_ID} u Funding Pips!",
            "account_email": EMAIL,
            "info": debug_info
        }), 200
    else:
        return jsonify({
            "status": "FAILED ❌",
            "message": "Nepodarilo se prihlasit k MatchTrader uctu.",
            "details": debug_info
        }), 400

@app.route('/webhook', methods=['POST'])
def webhook():
    """Přijímá signály z TradingView strategie"""
    try:
        raw_data = request.get_data(as_text=True)
        try:
            data = json.loads(raw_data)
        except Exception:
            data = request.form.to_dict() if request.form else {}

        # Načte ticker neboli symbol (podporuje "ticker" i "symbol")
        raw_symbol = data.get("ticker", data.get("symbol", ""))
        action = str(data.get("action", "")).upper()
        price = data.get("price", 0)

        trade_symbol = SYMBOL_MAP.get(raw_symbol, raw_symbol)

        print(f"📥 PŘIJAT SIGNÁL ZE STRATEGIE: {action} {trade_symbol} @ {price}")

        if "BUY" in action or "SELL" in action:
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
