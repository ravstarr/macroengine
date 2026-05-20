import schedule
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.fred_fetcher import run as fetch_fred
from data.market_fetcher import run as fetch_market
from data.news_fetcher import run as fetch_news
from data.backtester import run_backtest
from agents.orchestrator import run as run_orchestrator


def daily_pipeline():
    print("\n========================================")
    print("Running daily pipeline...")
    print("========================================")
    fetch_fred()
    fetch_market()
    fetch_news()
    run_backtest()
    run_orchestrator()
    print("Daily pipeline complete.")


schedule.every().day.at("06:00").do(daily_pipeline)
schedule.every(6).hours.do(fetch_news)

print("Scheduler running — pipeline fires daily at 06:00")
print("Press Ctrl+C to stop\n")

while True:
    schedule.run_pending()
    time.sleep(60)