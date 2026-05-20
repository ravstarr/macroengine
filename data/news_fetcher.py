import requests
import hashlib
from datetime import datetime
from api.config import NEWS_API_KEY
from api.database import SessionLocal
from api.models import NewsItem

BASE_URL = "https://newsapi.org/v2/everything"

QUERIES = [
    "Federal Reserve interest rates",
    "US inflation CPI",
    "GDP economic growth",
    "unemployment jobs report",
    "stock market S&P 500",
]

def fetch_headlines(query: str, page_size: int = 20):
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json().get("articles", [])


def make_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def store_articles(articles: list):
    db = SessionLocal()
    saved = 0
    skipped = 0
    try:
        for article in articles:
            url = article.get("url", "")
            if not url:
                continue

            url_hash = make_hash(url)
            exists = db.query(NewsItem).filter_by(url_hash=url_hash).first()
            if exists:
                skipped += 1
                continue

            published_raw = article.get("publishedAt")
            published_at = None
            if published_raw:
                try:
                    published_at = datetime.strptime(
                        published_raw, "%Y-%m-%dT%H:%M:%SZ"
                    )
                except ValueError:
                    pass

            record = NewsItem(
                headline=article.get("title", "")[:500],
                source=article.get("source", {}).get("name", ""),
                url_hash=url_hash,
                raw_text=article.get("description", ""),
                published_at=published_at,
            )
            db.add(record)
            saved += 1

        db.commit()
        print(f"  Saved {saved} articles, skipped {skipped} duplicates")
    except Exception as e:
        db.rollback()
        print(f"  Error storing articles: {e}")
    finally:
        db.close()


def run():
    print("Fetching financial news...")
    for query in QUERIES:
        print(f"Querying: '{query}'")
        try:
            articles = fetch_headlines(query)
            store_articles(articles)
        except Exception as e:
            print(f"  Failed: {e}")
    print("News fetch complete.")


if __name__ == "__main__":
    run()