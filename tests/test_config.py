from api.config import FRED_API_KEY, ALPHA_VANTAGE_KEY, NEWS_API_KEY

assert FRED_API_KEY, "FRED key missing"
assert ALPHA_VANTAGE_KEY, "Alpha Vantage key missing"
assert NEWS_API_KEY, "NewsAPI key missing"

print("All API keys loaded successfully — Day 1 complete!")
