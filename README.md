# 📈 Systematic Multi-Asset Sector Momentum Strategy Showcase

[![Quant Strategy Audit & CI](https://github.com/shubhamsinha1107/quant-momentum-showcase/actions/workflows/ci.yml/badge.svg)](https://github.com/shubhamsinha1107/quant-momentum-showcase/actions)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon%20Serverless-336791.svg)](https://neon.tech/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: Source-Available](https://img.shields.io/badge/License-Source--Available%20%7C%20Showcase%20Only-red.svg)](LICENSE)

An institutional quantitative research and performance attribution portal showcasing a **Multi-Horizon Systematic Momentum & Macro Volatility Strategy** across major **NSE Sector Indices and Precious Metals ETFs** (2020–2026).

Researched and engineered by **[Shubham Sinha](https://www.linkedin.com/in/shubham-sinha-7a3285300)** (*Investment Analyst | Portfolio Analytics & Quantitative Research*).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

---

## 🏛️ Open-Core Architecture & Quant Rigor

> ⚠️ **Portfolio Showcase Edition**: This repository is designed to showcase quantitative research methodology, macro sector momentum, empirical performance attribution, and full-stack software architecture.
> 
> To eliminate single-stock idiosyncratic drag and minimize data payload, this showcase executes on the **direct main sector indices and multi-asset ETFs** (with 1,012 executed fills prioritized from 3,205 candidate breakout signals over 6.8 years). Live broker execution credentials (Fyers/Zerodha API keys) and proprietary real-time order routing code are withheld. All backtest time-series, NAV equity curves, and trade execution logs reflect verified empirical engine outputs net of **15–20 bps round-trip transaction costs (STT, exchange fees, stamp duty, slippage)**.

---

## 🎯 Executive Strategy Summary

Retail momentum strategies in emerging markets typically suffer deep peak-to-trough drawdowns (-30% to -45%) during sudden regime shifts, consolidation chop, or rate-hike cycles. This framework resolves these vulnerabilities through three structural design principles:

1. **Lead-Lag Top-Down Sector Discovery**: Institutional capital flows into broad sectors (Autos, Realty, PSU Banks, Metals, Energy, IT) before individual stocks react. Trading confirmed trend breakouts across 30m and 60m timeframes yields high statistical expectancy.
2. **Multi-Asset Crisis Alpha**: Equities do not operate in isolation. When market-wide equity momentum deteriorates, capital systematically reallocates into **Physical Gold (`GOLDBEES`) and Silver (`SILVERBEES`) ETFs** alongside liquid cash, dampening overall portfolio volatility.
3. **Macro Volatility Regime Gate & Monthly Loss Circuit Breaker**: During extreme panic crashes (such as March 2020 COVID crash), equity breakout attempts are suppressed into cash/gold, turning March 2020 positive (**+2.4%**) and capping master portfolio maximum drawdown to **-9.2%** (versus **-38.4%** for the Nifty 50 benchmark).

---

## 📊 Empirical Performance Summary (2020 – 2026 Walk-Forward)

*Simulated results net of 15–20 bps round-trip transaction friction, execution slippage, cash equity (1.0x, zero leverage):*

| Metric | Master Multi-Slot Strategy (3 Slots, 30m) | Benchmark (Nifty 50 TR) | Quant Edge |
| :--- | :---: | :---: | :--- |
| **CAGR (Annualized)** | **+47.2%** | +15.2% | **+32.0% Alpha** |
| **Total Net Return** | **+1,288.2% (13.88x)** | +139.9% (2.40x) | **+1,148.3% Outperformance** |
| **Sharpe Ratio** | **2.95** | 0.88 | **Institutional Risk-Adjusted Quality** |
| **Sortino Ratio** | **4.18** | 1.12 | **Superior Downside Protection** |
| **Max Peak-to-Trough Drawdown** | **-9.2%** | **-38.4%** | **-29.2% Drawdown Compression** |
| **Calmar Ratio** | **5.13** | 0.40 | **12.8x Better Calmar** |
| **Market Beta vs Nifty 50** | **0.38** | 1.00 | **Low Market Beta Exposure** |
| **Time in Market (Exposure)** | **64.2%** | 100% | **Cash/Gold during Panic Drawdowns** |
| **Annual Portfolio Turnover** | **~148 cycles/year** | Buy & Hold | **~12 trades/month across 15 assets** |

---

## 🏆 Sector Index & ETF Attribution Breakdown

*Distinguishing standalone single-asset compounding (100% capital) vs realized portfolio P&L contribution under concurrent multi-slot execution:*

| Sector Index / ETF | Candidate Signals | Portfolio Fills | Win Rate | Standalone Return (100% Asset) | Portfolio P&L Contribution | Profit Factor |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **NIFTY REALTY** | 240 | 60 | 49.6% | **+956.1%** | **+34.0%** | **2.16** |
| **NIFTY SMALLCAP 250** | 253 | 92 | 51.8% | **+855.4%** | **+34.8%** | **2.51** |
| **NIFTY MIDCAP 150** | 261 | 92 | 51.0% | **+578.1%** | **+17.4%** | **2.43** |
| **SILVERBEES (Silver ETF)** | 164 | 67 | 47.0% | **+509.3%** | **+37.2%** | **2.52** |
| **NIFTY METAL** | 259 | 74 | 42.9% | **+482.0%** | **+6.2%** | **1.82** |
| **NIFTY PSU BANK** | 252 | 68 | 44.4% | **+409.9%** | **+21.0%** | **1.70** |
| **NIFTY ENERGY** | 251 | 64 | 49.4% | **+387.4%** | **+10.7%** | **2.07** |
| **NIFTY AUTO** | 257 | 91 | 46.3% | **+296.2%** | **+11.7%** | **1.80** |
| **GOLDBEES (Gold ETF)** | 187 | 83 | 46.5% | **+215.5%** | **+18.7%** | **2.23** |
| **FINNIFTY** | 264 | 69 | 42.8% | **+149.7%** | **+16.8%** | **1.57** |
| **NIFTY IT** | 265 | 95 | 42.3% | **+137.6%** | **+26.8%** | **1.50** |
| **NIFTY BANK** | 272 | 77 | 39.3% | **+115.5%** | **+24.4%** | **1.44** |
| **NIFTY HEALTHCARE** | 159 | 50 | 40.9% | **+78.1%** | **+1.3%** | **1.70** |
| **NIFTY CAPITAL MKT** | 61 | 16 | 36.1% | **+50.4%** | **+1.8%** | **1.99** |
| **NIFTY DEFENCE** | 60 | 14 | 41.7% | **+39.2%** | **+6.5%** | **1.75** |

---

## 🖥️ Interactive Showcase Features

- **Interactive Strategy Lab & Multi-Slot Simulator**: Visitors can dynamically adjust concurrent portfolio slots ($N \in [1..15]$), toggle signal horizons (`30m` vs `60m`), toggle the **Macro Crash Gate (ON/OFF)**, and select monthly risk limits (`-7%`, `-10%`, or unconstrained). Dynamic backtests execute in **< 15 ms** on pre-computed cross-sectional Sharpe ranks.
- **Dynamic Monthly Attribution Matrix**: Directly placed below the KPI strip; recalculates and color-codes monthly gains/losses dynamically on parameter changes.
- **Dynamic NAV Equity Curve**: Interactive Chart.js time-series comparing simulated portfolio allocation against the Nifty 50 Total Return Benchmark with default logarithmic scaling and regime annotations.
- **Underwater Drawdown Visualization**: Visual proof of capital preservation during the March 2020 COVID crash and 2022 inflation corrections.
- **Per-Asset Signal Generation & Attribution Table**: Clear breakdown distinguishing standalone single-asset compounding from portfolio P&L contributions.
- **Full Trade Execution Log (`/trades`)**: Filterable ledger (3,205 unfiltered candidate trade events) displaying discrete Buy & Sell signals, holding periods, and net returns by index.
- **Printable Strategy Explainer Memo (`/explainer?print=1`)**: Editorial research dossier with automatic print-to-PDF formatting.
- **Programmatic Simulation REST API**: `GET /api/simulate`, `POST /api/simulate`, and `GET /api/candidates` for automated quantitative research and integration.

---

## ⚡ Tech Stack & Architecture

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic
- **Database**: [Neon Serverless Postgres](https://neon.tech/) with zero-config fallback to embedded SQLite
- **Frontend**: Tailwind CSS (CDN), Chart.js, HTML5/Jinja2 Templates
- **Containerization**: Lightweight multi-stage Docker container
- **Hosting**: 1-click deployment on [Render.com](https://render.com/)

---

## 🚀 Quickstart & Local Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/shubhamsinha1107/quant-momentum-showcase.git
cd quant-momentum-showcase

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### 3. Run Application
```bash
python main.py
```
Visit `http://localhost:8000` in your web browser.

---

## 🌐 Deploy to Render.com with Neon Serverless Postgres

1. **Create Free Database on Neon**:
   - Go to [neon.tech](https://neon.tech/) and create a free PostgreSQL project.
   - Copy the `Pooled connection` string (e.g., `postgresql://...`).
2. **Deploy to Render**:
   - Link your GitHub repository to a new **Web Service** on Render.
   - In Environment Settings, add:
     - `DATABASE_URL`: Your Neon Postgres pooled connection string.
     - `PORT`: `8000`
   - Render builds the Docker container and launches the service. On boot, `seed_db.py` automatically initializes your Neon database.
3. **Prevent Cold Starts**:
   - Configure a free health check monitor (e.g., [UptimeRobot](https://uptimerobot.com/)) pinging `https://<your-render-app>.onrender.com/health` every 10 minutes.

---

## 👤 About the Author

**Shubham Sinha**  
*Investment Analyst | Portfolio Analytics & Quantitative Research*  
New Delhi, India  

- **LinkedIn**: [https://www.linkedin.com/in/shubham-sinha-7a3285300](https://www.linkedin.com/in/shubham-sinha-7a3285300)  
- **GitHub**: [https://github.com/shubhamsinha1107](https://github.com/shubhamsinha1107)  
- **Institutional Background**: Manages portfolio risk and quantitative analytics across an INR 400+ Cr single family office & conglomerate portfolio (equities, mutual funds, precious metals, and unlisted holdings).
