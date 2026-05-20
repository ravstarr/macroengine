from textblob import TextBlob
from datetime import datetime, timedelta
from api.database import SessionLocal
from api.models import NewsItem


def load_headlines(days_back: int = 7) -> list:
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(days=days_back)
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


def analyze_sentiment(headlines: list) -> list:
    results = []
    for headline in headlines:
        try:
            blob = TextBlob(headline)
            polarity = blob.sentiment.polarity
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            results.append({
                "headline": headline[:80],
                "sentiment": sentiment,
                "polarity": round(polarity, 4),
            })
        except Exception:
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
    confidence = round(max(bullish_pct, bearish_pct, neutral_pct), 2)

    return {
        "bullish": bullish_pct,
        "bearish": bearish_pct,
        "neutral": neutral_pct,
        "confidence": confidence,
        "total_articles": total,
    }


def run() -> dict:
    print("Running Sentiment Agent...")
    headlines = load_headlines(days_back=7)
    print(f"  Loaded {len(headlines)} headlines")

    if not headlines:
        print("  No headlines found")
        return {"error": "no headlines"}

    results = analyze_sentiment(headlines)
    aggregated = aggregate_scores(results)
    top = sorted(results, key=lambda x: x["polarity"], reverse=True)[:3]

    print(f"  Bullish: {aggregated['bullish'] * 100:.0f}%")
    print(f"  Bearish: {aggregated['bearish'] * 100:.0f}%")
    print(f"  Neutral: {aggregated['neutral'] * 100:.0f}%")
    print("Sentiment Agent complete.")

    return {
        "agent": "sentiment",
        "bullish": aggregated["bullish"],
        "bearish": aggregated["bearish"],
        "neutral": aggregated["neutral"],
        "confidence": aggregated["confidence"],
        "total_articles": aggregated["total_articles"],
        "top_bullish_headlines": [t["headline"] for t in top],
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    run()