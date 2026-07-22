import requests

# Přidat na začátek app.py k ostatním proměnným:
MATCHTRADER_API_URL = os.environ.get("MATCHTRADER_API_URL", "https://api.match-trader.com") # URL od brokera
MATCHTRADER_TOKEN = os.environ.get("MATCHTRADER_TOKEN")

def send_to_matchtrader(symbol: str, trade_type: str, volume: float, price: float = None) -> bool:
    """
    Odeslání příkazu přímo na MatchTrader REST API.
    """
    if not MATCHTRADER_TOKEN:
        logging.warning("⚠️ MATCHTRADER_TOKEN chybí v Environment Variables (simulační mód).")
        return True

    headers = {
        "Authorization": f"Bearer {MATCHTRADER_TOKEN}",
        "Content-Type": "application/json"
    }

    # Payload podle oficiální API dokumentace MatchTraderu
    payload = {
        "symbol": symbol,           # např. "US100"
        "cmd": trade_type,          # "BUY" nebo "SELL"
        "volume": volume,           # Počet lotů
        "type": "OPEN"
    }

    try:
        response = requests.post(f"{MATCHTRADER_API_URL}/open-position", json=payload, headers=headers, timeout=5)
        
        if response.status_code == 200:
            logging.info(f"✅ Pozice na MatchTraderu úspěšně otevřena: {trade_type} {volume} {symbol}")
            return True
        else:
            logging.error(f"❌ Chyba MatchTrader API [{response.status_code}]: {response.text}")
            return False

    except Exception as e:
        logging.error(f"❌ Výjimka při komunikaci s MatchTrader API: {e}")
        return False
