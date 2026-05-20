import requests
import time
from datetime import datetime
from api.config import ALPHA_VANTAGE_KEY
from api.database import SessionLocal
from api.models import MarketPrice

BASE_URL = "https://www.alphavantage.co/query"

SYMBOLS = {
    "SPY":  "S&P 500 ETF",
    "TLT":  "20Y Treasury Bond ETF",
    "GLD":  "Gold ETF",
    "USO":  "Oil ETF",
    "VIX":  "Volatility Index",
    "DXY":  "US Dollar Index",
}

def fetch_daily(symbol: str, limit: int = 30):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_KEY,
        "outputsize": "compact",
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    time_series = data.get("Time Series (Daily)", {})
    results = []
    for i, (date_str, values) in enumerate(time_series.items()):
        if i >= limit:
            break
        results.append({
            "date": datetime.strptime(date_str, "%Y-%m-%d"),
            "price": float(values["4. close"]),
            "volume": float(values["5. volume"]),
        })
    return results


def store_prices(symbol: str, name: str, records: list):
    db = SessionLocal()
    saved = 0
    try:
        for r in records:
            record = MarketPrice(
                symbol=symbol,
                name=name,
                price=r["price"],
                volume=r["volume"],
                date=r["date"],
            )
            db.add(record)
            saved += 1
        db.commit()
        print(f"  Saved {saved} records for {symbol}")
    except Exception as e:
        db.rollback()
        print(f"  Error saving {symbol}: {e}")
    finally:
        db.close()


def run():
    print("Fetching market data...")
    for symbol, name in SYMBOLS.items():
        print(f"Fetching {symbol} — {name}")
        try:
            records = fetch_daily(symbol)
            if records:
                store_prices(symbol, name, records)
            else:
                print(f"  No data returned for {symbol}")
        except Exception as e:
            print(f"  Failed {symbol}: {e}")
        time.sleep(12)
    print("Market fetch complete.")


if __name__ == "__main__":
    run()