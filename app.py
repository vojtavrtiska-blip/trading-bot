import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Převodní slovník symbolů pro Funding Pips / TradeLocker
SYMBOL_MAP = {
    "TVC:NDQ": "NAS100",
    "NDQ": "NAS100",
    "US100": "NAS100"
}

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON payload"}), 400

        raw_symbol = data.get("symbol", "")
        action = str(data.get("action", "")).upper()
        price = float(data.get("price", 0))

        # Převod symbolu
        trade_symbol = SYMBOL_MAP.get(raw_symbol, raw_symbol)

        print(f"📥 PŘIJAT SIGNÁL: {action} {trade_symbol} @ {price}")

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
