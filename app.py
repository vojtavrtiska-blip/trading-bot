import os
import logging
from flask import Flask, request, jsonify

# Nastavení logování pro Render konsoli
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)

# Načtení proměnných prostředí z Renderu
CTRADER_ACCOUNT_ID = os.environ.get("CTRADER_ACCOUNT_ID")
CTRADER_TOKEN = os.environ.get("CTRADER_TOKEN")
CTRADER_CLIENT_ID = os.environ.get("CTRADER_CLIENT_ID")
CTRADER_CLIENT_SECRET = os.environ.get("CTRADER_CLIENT_SECRET")

@app.route('/', methods=['GET'])
def home():
    """Základní health-check endpoint pro Render."""
    return jsonify({
        "status": "online",
        "bot": "US100 Pullback Master Webhook Server",
        "ctrader_configured": bool(CTRADER_ACCOUNT_ID and CTRADER_TOKEN)
    }), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint pro přijímání Alertů z TradingView."""
    try:
        data = request.get_json(force=True)
    except Exception as e:
        logging.error(f"Neplatný JSON formát: {e}")
        return jsonify({"status": "error", "message": "Invalid JSON format"}), 400

    if not data:
        logging.warning("Přijat prázdný požadavek.")
        return jsonify({"status": "error", "message": "Empty payload"}), 400

    logging.info(f"Přijatá zpráva z TradingView: {data}")

    # 1. Extrakce dat podle TV Alertu
    raw_ticker = data.get('ticker')
    raw_action = data.get('action')
    raw_contracts = data.get('contracts')
    raw_price = data.get('price')
    order_id = data.get('id')

    # Validační kontrola povinných polí
    if not all([raw_ticker, raw_action, raw_contracts]):
        logging.error("Chybí některé povinné parametry v JSONu.")
        return jsonify({"status": "error", "message": "Missing required fields (ticker, action, contracts)"}), 400

    # 2. Normalizace a přetypování dat
    action = str(raw_action).strip().lower()  # "buy" nebo "sell"
    
    try:
        contracts = float(raw_contracts)
        price = float(raw_price) if raw_price else None
    except ValueError as e:
        logging.error(f"Chyba při přetypování číselných hodnot: {e}")
        return jsonify({"status": "error", "message": "Invalid number format for contracts or price"}), 400

    # Mapování akce pro cTrader (BUY / SELL)
    trade_type = "BUY" if "buy" in action else "SELL" if "sell" in action else None

    if not trade_type:
        logging.error(f"Neznámý typ akce: {action}")
        return jsonify({"status": "error", "message": f"Unknown action type: {action}"}), 400

    # Mapování tickeru (např. TVC:NDQ -> US100)
    symbol = "US100" if "NDQ" in str(raw_ticker).upper() or "NDX" in str(raw_ticker).upper() else raw_ticker

    logging.info(f" Zpracovaný signál: {trade_type} {contracts} lotů {symbol} @ {price} (ID: {order_id})")

    # 3. Exekuce pokynu na cTraderu
    execution_success = send_to_ctrader(symbol=symbol, trade_type=trade_type, volume=contracts, price=price)

    if execution_success:
        return jsonify({
            "status": "success",
            "message": f"Order {trade_type} executed successfully",
            "data": {
                "symbol": symbol,
                "type": trade_type,
                "volume": contracts,
                "price": price
            }
        }), 200
    else:
        return jsonify({"status": "error", "message": "Failed to execute order on cTrader"}), 500


def send_to_ctrader(symbol: str, trade_type: str, volume: float, price: float = None) -> bool:
    """
    Funkce pro odeslání příkazu na cTrader API / FIX API / Webhook Bridge.
    """
    if not CTRADER_ACCOUNT_ID:
        logging.warning("⚠️ CTRADER_ACCOUNT_ID chybí v Environment Variables (mód simulace).")
        # Zde kód simuluje úspěch, dokud nedoplníš reálné proměnné na Renderu
        return True

    try:
        # ZDE NAVAZUJE VOLÁNÍ CTRADER OPEN API / FIX ENGINE
        # Příklad logování reálné exekuce:
        logging.info(f"Odesílám do cTraderu [Account: {CTRADER_ACCOUNT_ID}]: {trade_type} {volume} {symbol}")
        
        # ... tvoje logika / SDK volání cTraderu ...
        
        return True
    except Exception as e:
        logging.error(f"Chyba při komunikaci s cTrader API: {e}")
        return False


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
