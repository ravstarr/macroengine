import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime
from api.database import SessionLocal
from api.models import MacroIndicator


INDICATORS = {
    "GDP": {"label": "GDP Growth", "threshold": 0.02},
    "CPIAUCSL": {"label": "CPI Inflation", "threshold": 0.1},
    "UNRATE": {"label": "Unemployment", "threshold": 0.1},
    "FEDFUNDS": {"label": "Fed Funds Rate", "threshold": 0.05},
}


def load_series(series_id: str) -> pd.Series:
    db = SessionLocal()
    try:
        records = (
            db.query(MacroIndicator)
            .filter(MacroIndicator.series_id == series_id)
            .order_by(MacroIndicator.date.asc())
            .all()
        )
        if not records:
            return pd.Series(dtype=float)
        dates = [r.date for r in records]
        values = [r.value for r in records]
        return pd.Series(values, index=pd.DatetimeIndex(dates))
    finally:
        db.close()


def naive_forecast(series: pd.Series, step: int = 1) -> pd.Series:
    return series.shift(step)


def directional_accuracy(actual: pd.Series, predicted: pd.Series) -> float:
    actual_diff = actual.diff().dropna()
    pred_diff = predicted.diff().dropna()
    common = actual_diff.index.intersection(pred_diff.index)
    if len(common) < 2:
        return 0.0
    actual_dir = np.sign(actual_diff[common])
    pred_dir = np.sign(pred_diff[common])
    accuracy = (actual_dir == pred_dir).mean()
    return round(float(accuracy), 4)


def mean_absolute_error(actual: pd.Series, predicted: pd.Series) -> float:
    common = actual.index.intersection(predicted.index)
    if len(common) == 0:
        return 0.0
    mae = np.abs(actual[common] - predicted[common]).mean()
    return round(float(mae), 4)


def run_backtest() -> dict:
    print("Running Backtesting Engine...")
    results = {}

    for series_id, meta in INDICATORS.items():
        print(f"  Backtesting {series_id} — {meta['label']}")
        series = load_series(series_id)

        if len(series) < 4:
            print(f"    Skipping — not enough data")
            continue

        predicted = naive_forecast(series, step=1)
        dir_acc = directional_accuracy(series, predicted)
        mae = mean_absolute_error(series, predicted)

        accuracy_pct = round(dir_acc * 100, 1)
        current = round(float(series.iloc[-1]), 3)
        previous = round(float(series.iloc[-2]), 3)
        actual_direction = "up" if current > previous else "down"

        results[series_id] = {
            "label": meta["label"],
            "directional_accuracy": accuracy_pct,
            "mae": mae,
            "current_value": current,
            "previous_value": previous,
            "actual_direction": actual_direction,
            "observations": len(series),
        }

        print(f"    Directional accuracy: {accuracy_pct}%")
        print(f"    MAE: {mae}")

    overall = round(
        np.mean([v["directional_accuracy"] for v in results.values()]), 1
    ) if results else 0.0

    print(f"\n  Overall backtest accuracy: {overall}%")
    print("Backtesting Engine complete.")

    return {
        "results": results,
        "overall_accuracy": overall,
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    run_backtest()
