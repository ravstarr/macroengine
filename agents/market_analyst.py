import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from api.database import SessionLocal
from api.models import MarketPrice

REGIME_LABELS = {0: "bear", 1: "neutral", 2: "bull"}

def load_market_data() -> pd.DataFrame:
    db = SessionLocal()
    try:
        records = (
            db.query(MarketPrice)
            .filter(MarketPrice.symbol == "SPY")
            .order_by(MarketPrice.date.asc())
            .all()
        )
        df = pd.DataFrame([{
            "date": r.date,
            "price": r.price,
            "volume": r.volume,
        } for r in records])
        return df
    finally:
        db.close()


def build_features(df: pd.DataFrame) -> np.ndarray:
    df = df.copy()
    df["returns"] = df["price"].pct_change()
    df["volatility"] = df["returns"].rolling(5).std()
    df["momentum"] = df["price"] / df["price"].shift(5) - 1
    df = df.dropna()

    features = df[["returns", "volatility", "momentum"]].values
    scaler = StandardScaler()
    return scaler.fit_transform(features), df


def detect_regime(features: np.ndarray) -> tuple:
    model = GaussianHMM(
        n_components=3,
        covariance_type="full",
        n_iter=1000,
        random_state=42,
    )
    model.fit(features)
    states = model.predict(features)
    current_state = int(states[-1])

    means = model.means_[:, 0]
    sorted_states = np.argsort(means)
    regime_map = {
        sorted_states[0]: "bear",
        sorted_states[1]: "neutral",
        sorted_states[2]: "bull",
    }
    regime = regime_map[current_state]

    log_prob = model.score(features[-10:])
    confidence = min(abs(log_prob) / 20, 1.0)
    confidence = round(confidence, 2)

    return regime, confidence, states, regime_map


def get_signals(df: pd.DataFrame) -> list:
    signals = []
    latest = df.iloc[-1]
    prev = df.iloc[-5]

    if latest["price"] > prev["price"]:
        signals.append({"signal": "Price trending up 5 days", "type": "bullish"})
    else:
        signals.append({"signal": "Price trending down 5 days", "type": "bearish"})

    if latest["volatility"] > df["volatility"].mean() * 1.5:
        signals.append({"signal": "High volatility detected", "type": "warning"})
    else:
        signals.append({"signal": "Volatility within normal range", "type": "neutral"})

    if latest["momentum"] > 0.02:
        signals.append({"signal": "Strong positive momentum", "type": "bullish"})
    elif latest["momentum"] < -0.02:
        signals.append({"signal": "Strong negative momentum", "type": "bearish"})
    else:
        signals.append({"signal": "Momentum neutral", "type": "neutral"})

    return signals


def run() -> dict:
    print("Running Market Analyst Agent...")
    df = load_market_data()

    if df.empty or len(df) < 10:
        print("  Not enough data to run agent")
        return {"error": "insufficient data"}

    features, df_clean = build_features(df)
    regime, confidence, states, regime_map = detect_regime(features)
    signals = get_signals(df_clean)

    result = {
        "agent": "market_analyst",
        "regime": regime,
        "confidence": confidence,
        "signals": signals,
        "timestamp": datetime.utcnow().isoformat(),
    }

    print(f"  Regime detected: {regime.upper()}")
    print(f"  Confidence: {confidence}")
    print(f"  Signals: {[s['signal'] for s in signals]}")
    print("Market Analyst Agent complete.")
    return result


if __name__ == "__main__":
    result = run()