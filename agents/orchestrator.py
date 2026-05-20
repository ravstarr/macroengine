import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from agents.market_analyst import run as run_market
from agents.sentiment_agent import run as run_sentiment
from agents.macro_modeler import run as run_macro


def compute_overall_confidence(agents: list) -> float:
    confidences = [a["confidence"] for a in agents if "confidence" in a]
    if not confidences:
        return 0.0
    return round(sum(confidences) / len(confidences), 2)


def detect_disagreements(market: dict, sentiment: dict, macro: dict) -> list:
    disagreements = []

    market_bullish = market.get("regime") == "bull"
    sentiment_bullish = sentiment.get("bullish", 0) > sentiment.get("bearish", 0)

    if market_bullish != sentiment_bullish:
        disagreements.append({
            "type": "regime_vs_sentiment",
            "detail": f"Market says {market.get('regime')} but sentiment is "
                      f"{'bullish' if sentiment_bullish else 'bearish'}",
            "severity": "medium",
        })

    gdp = macro.get("forecasts", {}).get("GDP", {})
    unrate = macro.get("forecasts", {}).get("UNRATE", {})
    if gdp.get("direction") == "up" and unrate.get("direction") == "up":
        disagreements.append({
            "type": "gdp_unemployment",
            "detail": "GDP and unemployment both rising — unusual signal",
            "severity": "low",
        })

    fedfunds = macro.get("forecasts", {}).get("FEDFUNDS", {})
    cpi = macro.get("forecasts", {}).get("CPIAUCSL", {})
    if fedfunds.get("direction") == "down" and cpi.get("direction") == "up":
        disagreements.append({
            "type": "rate_inflation",
            "detail": "Rates falling while inflation rising — watch closely",
            "severity": "high",
        })

    return disagreements


def blend_outlook(market: dict, sentiment: dict, macro: dict) -> str:
    scores = {"bullish": 0, "bearish": 0, "neutral": 0}

    if market.get("regime") == "bull":
        scores["bullish"] += market.get("confidence", 0.5)
    elif market.get("regime") == "bear":
        scores["bearish"] += market.get("confidence", 0.5)
    else:
        scores["neutral"] += market.get("confidence", 0.5)

    scores["bullish"] += sentiment.get("bullish", 0) * sentiment.get("confidence", 0.5)
    scores["bearish"] += sentiment.get("bearish", 0) * sentiment.get("confidence", 0.5)
    scores["neutral"] += sentiment.get("neutral", 0) * sentiment.get("confidence", 0.5)

    gdp_dir = macro.get("forecasts", {}).get("GDP", {}).get("direction", "")
    if gdp_dir == "up":
        scores["bullish"] += macro.get("confidence", 0.5) * 0.5
    elif gdp_dir == "down":
        scores["bearish"] += macro.get("confidence", 0.5) * 0.5

    return max(scores, key=scores.get)


def run() -> dict:
    print("=" * 50)
    print("Running Orchestrator Agent...")
    print("=" * 50)

    print("\n[1/3] Market Analyst Agent")
    market = run_market()

    print("\n[2/3] Sentiment Agent")
    sentiment = run_sentiment()

    print("\n[3/3] Macro Modeler Agent")
    macro = run_macro()

    print("\n Blending outputs...")
    overall_confidence = compute_overall_confidence([
        {"confidence": market.get("confidence", 0)},
        {"confidence": sentiment.get("confidence", 0)},
        {"confidence": macro.get("confidence", 0)},
    ])

    disagreements = detect_disagreements(market, sentiment, macro)
    outlook = blend_outlook(market, sentiment, macro)

    result = {
        "agent": "orchestrator",
        "outlook": outlook,
        "overall_confidence": overall_confidence,
        "disagreements": disagreements,
        "market": market,
        "sentiment": sentiment,
        "macro": macro,
        "timestamp": datetime.utcnow().isoformat(),
    }

    print("\n" + "=" * 50)
    print(f"  FINAL OUTLOOK:     {outlook.upper()}")
    print(f"  OVERALL CONFIDENCE: {overall_confidence}")
    print(f"  DISAGREEMENTS:     {len(disagreements)} detected")
    for d in disagreements:
        print(f"    [{d['severity'].upper()}] {d['detail']}")
    print("=" * 50)

    return result


if __name__ == "__main__":
    run()
