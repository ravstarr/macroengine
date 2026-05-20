from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import run as run_orchestrator
from agents.market_analyst import run as run_market
from agents.sentiment_agent import run as run_sentiment
from agents.macro_modeler import run as run_macro
from data.backtester import run_backtest

app = FastAPI(title="MacroEngine API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cache = {}


def get_cached(key: str, ttl_seconds: int = 300):
    if key in cache:
        entry = cache[key]
        age = (datetime.utcnow() - entry["timestamp"]).seconds
        if age < ttl_seconds:
            return entry["data"]
    return None


def set_cache(key: str, data: dict):
    cache[key] = {"data": data, "timestamp": datetime.utcnow()}


@app.get("/")
def root():
    return {"status": "ok", "message": "MacroEngine API is running"}


@app.head("/")
def root_head():
    return {}


@app.get("/forecast")
def get_forecast():
    cached = get_cached("forecast")
    if cached:
        return cached
    result = run_orchestrator()
    set_cache("forecast", result)
    return result


@app.get("/market")
def get_market():
    cached = get_cached("market")
    if cached:
        return cached
    result = run_market()
    set_cache("market", result)
    return result


@app.get("/sentiment")
def get_sentiment():
    cached = get_cached("sentiment")
    if cached:
        return cached
    result = run_sentiment()
    set_cache("sentiment", result)
    return result


@app.get("/macro")
def get_macro():
    cached = get_cached("macro")
    if cached:
        return cached
    result = run_macro()
    set_cache("macro", result)
    return result


@app.get("/backtest")
def get_backtest():
    cached = get_cached("backtest")
    if cached:
        return cached
    result = run_backtest()
    set_cache("backtest", result)
    return result


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cached_keys": list(cache.keys()),
    }