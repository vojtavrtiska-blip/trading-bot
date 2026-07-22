import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

EMAIL = os.environ.get("MATCHTRADER_EMAIL")
ACCOUNT_ID = os.environ.get("MATCHTRADER_ACCOUNT")
PASSWORD = os.environ.get("MATCHTRADER_PASSWORD")
SERVER = os.environ.get("MATCHTRADER_SERVER", "FundingPips")

BASE_URL = "https://gtrader.fundingpips.com/api"

SYMBOL_MAP = {
    "TVC:NDQ": "NAS100",
    "NDQ": "NAS100",
    "US100": "NAS100"
}

def get_auth_token():
    try:
        url = f"{BASE_URL}/auth/login"
        payload = {
            "email": EMAIL,
            "password": PASSWORD,
            "server": SERVER
        }
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            return res.json().get("token"), res.json()
        else:
            return None, f"Chyba {res.status_code}: {res.text}"
    except Exception as e:
        return None, str(e)

@app.route('/test', methods=['GET'])
def test_connection():
    """Testovací adresa pro overeni spojeni s MatchTrader uctem"""
    token, debug_info = get_auth_token()
    if token:
        return jsonify({
            "status": "SUCCESS ✅",
            "message": f"Uspesne pripojeno k uctu {ACCOUNT_ID} u Funding Pips!",
            "account_email": EMAIL,
            "raw_response": debug_info
        }), 200
    else:
        return jsonify({
            "status": "FAILED ❌",
            "message": "Nepodarilo se prihlasit k MatchTrader uctu.",
            "details": debug_info
        }), 400

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
