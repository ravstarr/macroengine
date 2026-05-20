import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.market_analyst import run as run_market
from agents.sentiment_agent import run as run_sentiment
from agents.macro_modeler import run as run_macro
from agents.orchestrator import run as run_orchestrator


def test_market_analyst():
    print("Testing Market Analyst Agent...")
    result = run_market()
    assert "agent" in result
    assert result["agent"] == "market_analyst"
    assert "regime" in result
    assert result["regime"] in ["bull", "bear", "neutral"]
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
    assert "signals" in result
    assert isinstance(result["signals"], list)
    print("  Market Analyst — PASSED")


def test_sentiment_agent():
    print("Testing Sentiment Agent...")
    result = run_sentiment()
    assert "agent" in result
    assert result["agent"] == "sentiment"
    assert "bullish" in result
    assert "bearish" in result
    assert "neutral" in result
    total = result["bullish"] + result["bearish"] + result["neutral"]
    assert 0.95 <= round(total, 1) <= 1.05
    print("  Sentiment Agent — PASSED")


def test_macro_modeler():
    print("Testing Macro Modeler Agent...")
    result = run_macro()
    assert "agent" in result
    assert result["agent"] == "macro_modeler"
    assert "forecasts" in result
    assert len(result["forecasts"]) > 0
    for key, val in result["forecasts"].items():
        assert "current" in val
        assert "forecast_6mo" in val
        assert "direction" in val
        assert val["direction"] in ["up", "down"]
    print("  Macro Modeler — PASSED")


def test_orchestrator():
    print("Testing Orchestrator Agent...")
    result = run_orchestrator()
    assert "agent" in result
    assert result["agent"] == "orchestrator"
    assert "outlook" in result
    assert result["outlook"] in ["bullish", "bearish", "neutral"]
    assert "overall_confidence" in result
    assert "disagreements" in result
    assert "market" in result
    assert "sentiment" in result
    assert "macro" in result
    print("  Orchestrator — PASSED")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  RUNNING INTEGRATION TESTS")
    print("=" * 50 + "\n")
    test_market_analyst()
    test_sentiment_agent()
    test_macro_modeler()
    test_orchestrator()
    print("\n" + "=" * 50)
    print("  ALL TESTS PASSED — Phase 2 complete!")
    print("=" * 50 + "\n")