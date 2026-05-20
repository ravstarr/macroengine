# MacroEngine — AI-Powered Macroeconomic Forecasting System

A multi-agent AI system that produces real-time macroeconomic forecasts by 
blending market analysis, NLP sentiment analysis, and statistical modeling.

## Architecture
- **Market Analyst Agent** — Hidden Markov Model for market regime detection
- **Sentiment Agent** — NLP analysis of 100+ financial headlines daily
- **Macro Modeler Agent** — Vector Autoregression forecasting GDP, CPI, unemployment
- **Orchestrator Agent** — Blends all agents into a unified forecast

## Tech Stack
Python · FastAPI · PostgreSQL · scikit-learn · statsmodels · TextBlob · React · Vite

## Live API
https://macroengine.onrender.com/docs

## Setup
```bash
pip install -r requirements.txt
python api/database.py
python data/fred_fetcher.py
python -m uvicorn api.main:app --reload
```

## Dashboard
```bash
cd frontend && npm install && npm run dev
```