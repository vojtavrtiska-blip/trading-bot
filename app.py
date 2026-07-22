import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SYMBOL_MAP = {
    "TVC:NDQ": "NAS100",
    "NDQ": "NAS100",
    "US100": "NAS100"
}

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
