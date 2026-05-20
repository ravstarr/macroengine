import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller
from datetime import datetime
from api.database import SessionLocal
from api.models import MacroIndicator

SERIES_TO_MODEL = ["CPIAUCSL", "UNRATE", "FEDFUNDS", "GDP"]


def load_macro_data() -> pd.DataFrame:
    db = SessionLocal()
    try:
        records = (
            db.query(MacroIndicator)
            .filter(MacroIndicator.series_id.in_(SERIES_TO_MODEL))
            .order_by(MacroIndicator.date.asc())
            .all()
        )
        rows = [{"date": r.date, "series_id": r.series_id, "value": r.value}
                for r in records]
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame()
        df = df.pivot_table(index="date", columns="series_id", values="value")
        df = df.ffill().dropna()
        return df
    finally:
        db.close()


def make_stationary(df: pd.DataFrame) -> pd.DataFrame:
    stationary = pd.DataFrame(index=df.index)
    for col in df.columns:
        result = adfuller(df[col].dropna())
        if result[1] > 0.05:
            stationary[col] = df[col].diff()
        else:
            stationary[col] = df[col]
    return stationary.dropna()


def run_var_model(df: pd.DataFrame, steps: int = 6) -> dict:
    model = VAR(df)
    max_lags = min(2, len(df) // (len(df.columns) * 2) - 1)
    max_lags = max(1, max_lags)
    results = model.fit(maxlags=max_lags, ic="aic")

    forecast = results.forecast(df.values[-results.k_ar:], steps=steps)
    forecast_df = pd.DataFrame(
        forecast, columns=df.columns,
        index=pd.date_range(start=df.index[-1], periods=steps + 1, freq="MS")[1:]
    )

    stderr = np.std(results.resid, axis=0)
    upper = forecast_df + 1.645 * stderr
    lower = forecast_df - 1.645 * stderr

    return {
        "forecast": forecast_df,
        "upper": upper,
        "lower": lower,
        "lag_order": results.k_ar,
    }


def build_output(raw_df: pd.DataFrame, var_results: dict) -> dict:
    forecast_df = var_results["forecast"]
    upper_df = var_results["upper"]
    lower_df = var_results["lower"]

    forecasts = {}
    for col in forecast_df.columns:
        current = float(raw_df[col].iloc[-1])
        predicted_diff = float(forecast_df[col].iloc[-1])
        predicted = current + (predicted_diff * var_results["lag_order"])
        upper = current + (float(upper_df[col].iloc[-1]) * var_results["lag_order"])
        lower = current + (float(lower_df[col].iloc[-1]) * var_results["lag_order"])
        direction = "up" if predicted > current else "down"
        change = round(predicted - current, 3)

        forecasts[col] = {
            "current": round(current, 3),
            "forecast_6mo": round(predicted, 3),
            "upper_bound": round(upper, 3),
            "lower_bound": round(lower, 3),
            "direction": direction,
            "change": change,
        }

    confidence = min(0.95, max(0.5, 1 - (var_results["lag_order"] / 10)))
    return {"forecasts": forecasts, "confidence": round(confidence, 2)}


def run() -> dict:
    print("Running Macro Modeler Agent...")
    raw_df = load_macro_data()

    if raw_df.empty or len(raw_df) < 6:
        print("  Not enough data to run VAR model")
        return {"error": "insufficient data"}

    print(f"  Loaded {len(raw_df)} observations across {len(raw_df.columns)} series")
    stationary_df = make_stationary(raw_df)
    print(f"  Running VAR model...")
    var_results = run_var_model(stationary_df)
    output = build_output(raw_df, var_results)

    print(f"  Lag order selected: {var_results['lag_order']}")
    print(f"  Confidence: {output['confidence']}")
    for series, vals in output["forecasts"].items():
        arrow = "↑" if vals["direction"] == "up" else "↓"
        print(f"  {series}: {vals['current']} → {vals['forecast_6mo']} {arrow}")

    print("Macro Modeler Agent complete.")

    return {
        "agent": "macro_modeler",
        "forecasts": output["forecasts"],
        "confidence": output["confidence"],
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    run()