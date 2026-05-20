import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from data.fred_fetcher import run as fetch_fred
from data.market_fetcher import run as fetch_market
from data.news_fetcher import run as fetch_news
from data.backtester import run_backtest
from agents.orchestrator import run as run_orchestrator


def run_pipeline(skip_fetch: bool = False) -> dict:
    print("\n" + "=" * 60)
    print("  MACROENGINE FULL PIPELINE")
    print(f"  Started: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    if not skip_fetch:
        print("\n STEP 1: Fetching fresh data...")
        fetch_fred()
        fetch_market()
        fetch_news()
    else:
        print("\n STEP 1: Skipping data fetch (using cached data)")

    print("\n STEP 2: Running backtest...")
    backtest = run_backtest()

    print("\n STEP 3: Running agent pipeline...")
    forecast = run_orchestrator()

    result = {
        "pipeline_run": datetime.utcnow().isoformat(),
        "backtest": backtest,
        "forecast": forecast,
    }

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print(f"  Outlook:    {forecast.get('outlook', 'unknown').upper()}")
    print(f"  Confidence: {forecast.get('overall_confidence', 0)}")
    print(f"  Accuracy:   {backtest.get('overall_accuracy', 0)}%")
    print("=" * 60 + "\n")

    return result


if __name__ == "__main__":
    run_pipeline(skip_fetch=True)
    