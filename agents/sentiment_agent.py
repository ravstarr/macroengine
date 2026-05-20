import torch
import numpy as np
from transformers import BertTokenizer, BertForSequenceClassification
from datetime import datetime, timedelta
from api.database import SessionLocal
from api.models import NewsItem

MODEL_NAME = "ProsusAI/finbert"

def load_model():
    print("  Loading FinBERT model...")
    tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
    model = BertForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    print("  FinBERT loaded.")
    return tokenizer, model


def load_headlines(days_back: int = 7) -> list:
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        records = (
            db.query(NewsItem)
            .filter(NewsItem.published_at >= cutoff)
            .order_by(NewsItem.published_at.desc())
            .limit(100)
            .all()
        )
        return [r.headline for r in records if r.headline]
    finally:
        db.close()


def analyze_sentiment(headlines: list, tokenizer, model) -> list:
    results = []
    for headline in headlines:
        try:
            inputs = tokenizer(
                headline,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            with torch.no_grad():
                outputs = model(**inputs)

            probs = torch.softmax(outputs.logits, dim=1).squeeze()
            labels = ["positive", "negative", "neutral"]
            scores = {labels[i]: round(float(probs[i]), 4) for i in range(3)}
            predicted = labels[int(torch.argmax(probs))]

            results.append({
                "headline": headline[:80],
                "sentiment": predicted,
                "scores": scores,
            })
        except Exception as e:
            continue
    return results


def aggregate_scores(results: list) -> dict:
    if not results:
        return {"bullish": 0.0, "bearish": 0.0, "neutral": 1.0, "confidence": 0.0}

    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for r in results:
        counts[r["sentiment"]] += 1

    total = len(results)
    bullish_pct = round(counts["positive"] / total, 2)
    bearish_pct = round(counts["negative"] / total, 2)
    neutral_pct = round(counts["neutral"] / total, 2)

    dominant = max(bullish_pct, bearish_pct, neutral_pct)
    confidence = round(dominant, 2)

    return {
        "bullish": bullish_pct,
        "bearish": bearish_pct,
        "neutral": neutral_pct,
        "confidence": confidence,
        "total_articles": total,
    }


def run() -> dict:
    print("Running Sentiment Agent...")
    tokenizer, model = load_model()

    headlines = load_headlines(days_back=7)
    print(f"  Loaded {len(headlines)} headlines from last 7 days")

    if not headlines:
        print("  No headlines found — run news_fetcher.py first")
        return {"error": "no headlines"}

    print("  Analysing sentiment...")
    results = analyze_sentiment(headlines, tokenizer, model)
    aggregated = aggregate_scores(results)

    top = sorted(results, key=lambda x: x["scores"]["positive"], reverse=True)[:3]
    print(f"  Bullish: {aggregated['bullish'] * 100:.0f}%")
    print(f"  Bearish: {aggregated['bearish'] * 100:.0f}%")
    print(f"  Neutral: {aggregated['neutral'] * 100:.0f}%")
    print(f"  Confidence: {aggregated['confidence']}")
    print(f"  Based on {aggregated['total_articles']} articles")
    print("Sentiment Agent complete.")

    return {
        "agent": "sentiment",
        "bullish": aggregated["bullish"],
        "bearish": aggregated["bearish"],
        "neutral": aggregated["neutral"],
        "confidence": aggregated["confidence"],
        "total_articles": aggregated["total_articles"],
        "top_bullish_headlines": [t["headline"] for t in top],
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    run()