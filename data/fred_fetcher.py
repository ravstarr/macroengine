import requests
import hashlib
from datetime import datetime
from api.config import FRED_API_KEY
from api.database import SessionLocal
from api.models import MacroIndicator

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "GDP":     "Gross Domestic Product",
    "CPIAUCSL": "Consumer Price Index",
    "UNRATE":  "Unemployment Rate",
    "FEDFUNDS": "Federal Funds Rate",
    "T10Y2Y":  "10Y-2Y Treasury Spread",
    "PCEPILFE": "Core PCE Inflation",
}

def fetch_series(series_id: str, limit: int = 12):
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json().get("observations", [])


def store_observations(series_id: str, name: str, observations: list):
    db = SessionLocal()
    saved = 0
    try:
        for obs in observations:
            if obs["value"] == ".":
                continue
            record = MacroIndicator(
                series_id=series_id,
                name=name,
                value=float(obs["value"]),
                date=datetime.strptime(obs["date"], "%Y-%m-%d"),
            )
            db.add(record)
            saved += 1
        db.commit()
        print(f"  Saved {saved} records for {series_id}")
    except Exception as e:
        db.rollback()
        print(f"  Error saving {series_id}: {e}")
    finally:
        db.close()


def run():
    print("Fetching FRED macro data...")
    for series_id, name in SERIES.items():
        print(f"Fetching {series_id} — {name}")
        try:
            observations = fetch_series(series_id)
            store_observations(series_id, name, observations)
        except Exception as e:
            print(f"  Failed to fetch {series_id}: {e}")
    print("FRED fetch complete.")


if __name__ == "__main__":
    run()