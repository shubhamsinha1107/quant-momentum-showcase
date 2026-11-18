# 📈 Sector Index Momentum Strategy Showcase

[![Quant Strategy Audit & CI](https://github.com/shubhamsinha1107/quant-momentum-showcase/actions/workflows/ci.yml/badge.svg)](https://github.com/shubhamsinha1107/quant-momentum-showcase/actions)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: Source-Available](https://img.shields.io/badge/License-Source--Available%20%7C%20Showcase%20Only-red.svg)](LICENSE)

A research and performance portal for a **rule-based intraday-signal momentum strategy** that trades whole **NSE sector and broad indices plus Gold and Silver ETFs**: no single stocks.

Researched and engineered by **[Shubham Sinha](https://www.linkedin.com/in/shubham-sinha-7a3285300)** (*Investment Analyst | Portfolio Analytics & Quantitative Research*).

**Live site:** https://quant.80-225-254-110.sslip.io/

---

## What this repository shows

> ⚠️ **Showcase edition.** The numbers come from the same strategy code that runs a live paper-trading bot, applied **directly to the index / ETF price series** (30-minute bars). No proxy stocks are used. Broker credentials, order routing and the signal code itself are not in this repository.
>
> **Published with a 30-day delay.** The site is refreshed every trading evening but only shows data up to 30 days ago, so trades that closed in the last month appear later.

- **4 strategies**, each holding **at most one index or ETF at a time**, chosen by recent risk-adjusted momentum on 30- or 60-minute bars, and exited when that edge fades.
- A **market-wide risk-off filter** keeps them in cash during stress.
- Capital is split across the strategies at fixed weights and **rebalanced monthly**. No leverage, no shorting.

---

## 📊 Results snapshot (1 Jan 2020 – 19 Oct 2026)

*These figures are a snapshot taken when this README was written; the [live site](https://quant.80-225-254-110.sslip.io/) is always current. All returns are net of a **0.20% round-trip cost** per trade. Positions, including trades still open, are marked at each day's close. Sharpe and Sortino use daily returns × √252 with a risk-free rate of 0.*

| Metric | Combined portfolio | Nifty 50 (price index) |
| :--- | ---: | ---: |
| CAGR | **+49.7%** | +9.7% |
| Total return | **+1,450%** | +88% |
| Max drawdown | **−13.3%** | −38.2% |
| Volatility (annualised) | 16.3% | 17.6% |
| Sharpe | **2.60** | 0.62 |
| Sortino | 4.49 | 0.85 |
| Calmar | 3.73 | 0.25 |
| Beta to Nifty 50 | 0.25 | 1.00 |
| Days with a position | 93.8% | 100% |
| Closed trades / win rate | 781 / 47.9% | |
| Profit factor / average trade | 2.75 / +1.42% | |

### Calendar years

The rules were developed on 2020–2024 and fixed on **31 Dec 2024**, so 2025 onward is out of sample.

| Year | Strategy | Nifty 50 | Max DD in year | Trades closed | Sample |
| :--- | ---: | ---: | ---: | ---: | :--- |
| 2020 | +62.3% | +14.6% | −8.1% | 104 | In sample |
| 2021 | +52.4% | +24.3% | −8.1% | 139 | In sample |
| 2022 | +17.1% | +4.3% | −12.7% | 95 | In sample |
| 2023 | +31.4% | +19.9% | −9.2% | 119 | In sample |
| 2024 | +35.7% | +8.9% | −6.7% | 133 | In sample |
| 2025 | +145.4% | +10.4% | −4.1% | 89 | Out of sample |
| 2026 (to 19 Oct) | +22.3% | −12.4% | −11.7% | 102 | Out of sample |

**About 2025:** most of the gain came from the Silver ETF (SILVERBEES rose from about ₹150 to ₹223 in Nov–Dec 2025), and three strategies held it at the same time. Strategies are allowed to hold the same asset at once, so concentration can be high.

### Strategies (each run alone with 100% of capital)

| Strategy | Signals | Portfolio weight | Trades | Win | CAGR | Max DD | Sharpe | Profit factor |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rapid Sector Momentum | 30-min | 28.6% | 294 | 46.9% | +68.4% | −26.4% | 2.46 | 2.64 |
| Midcap Satellite | 30-min | 14.3% | 176 | 49.4% | +23.7% | −11.6% | 2.04 | 2.54 |
| Core Sector Momentum | 60-min | 28.6% | 170 | 44.7% | +46.6% | −26.4% | 1.83 | 2.53 |
| Multi-Asset Hedge | 60-min | 28.6% | 141 | 51.8% | +44.4% | −16.2% | 2.07 | 3.56 |

### By index / ETF

*"Contribution" is the sum of each trade's net return × its strategy's weight, in % of capital (not compounded).*

| Index / ETF | Trades | Win | Avg trade | Contribution | Profit factor |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Silver ETF (SILVERBEES) | 76 | 52.6% | +3.79% | +82.2% | 5.40 |
| Gold ETF (GOLDBEES) | 109 | 52.3% | +1.23% | +38.5% | 2.63 |
| Nifty Realty | 52 | 40.4% | +1.83% | +27.1% | 2.53 |
| Nifty Midcap 50 | 126 | 51.6% | +0.98% | +26.4% | 2.58 |
| Nifty PSU Bank | 67 | 43.3% | +1.36% | +26.0% | 2.19 |
| Nifty Smallcap 50 | 129 | 47.3% | +1.05% | +25.8% | 2.78 |
| Nifty Metal | 62 | 37.1% | +1.36% | +24.1% | 2.19 |
| Nifty India Defence | 16 | 62.5% | +3.17% | +14.5% | 5.38 |
| Nifty Healthcare | 28 | 64.3% | +1.62% | +13.0% | 6.37 |
| Nifty IT | 23 | 39.1% | +1.34% | +8.8% | 2.65 |
| Nifty Bank | 16 | 56.2% | +1.08% | +4.9% | 1.87 |
| Nifty Auto | 28 | 46.4% | +0.58% | +4.6% | 1.79 |
| Nifty Financial Services | 8 | 62.5% | +1.28% | +2.9% | 3.82 |
| Nifty Capital Markets | 3 | 66.7% | +0.67% | +0.6% | 1.78 |
| Nifty Energy | 38 | 31.6% | −0.39% | −4.3% | 0.60 |

---

## ⚠️ Limits — read before quoting these numbers

- **A model, not broker fills.** Results come from index prices at bar closes. They are not audited or broker-reported returns.
- **Indices can't be bought directly.** In practice you would use an ETF or futures, which adds tracking error and different costs.
- **In-sample years.** 2020–2024 are the years the rules were built on. Only 2025 onward is out of sample.
- **Not the full live bot.** The live bot also runs a monthly stock-basket rotation strategy. It is left out here because it isn't index-level, so these numbers differ from the bot's own model.
- **Not a prediction.** Past results don't predict future returns. This is not investment advice.

---

## 🖥️ Site features

- **Strategy Lab:** re-runs the published trades with your choices:
  - which strategies to include (weights rescaled to 100%)
  - which indices may be traded
  - cost per round trip
  - a monthly loss stop

  At default settings it reproduces the published numbers exactly. The loss stop uses only past closes, so there is no look-ahead. A trade in an index you switch off is skipped and that strategy stays in cash; it does not swap in another index.
- **Daily-marked equity curve and drawdown** vs Nifty 50, plus a monthly return matrix.
- **Calendar-year chart** with the out-of-sample years marked, and **contribution by index**.
- **Trade log (`/trades`):** every closed trade, filterable by index and strategy.
- **Printable memo (`/explainer`):** a one-page A4 summary.
- **JSON API:**
  - `/api/meta`, `/api/summary`, `/api/indices`, `/api/annual`, `/api/monthly`, `/api/equity`, `/api/trades`
  - `GET|POST /api/simulate` (`strategies`, `universe`, `cost`, `monthly_stop`)
  - `/health` (reports the data cut-off date)

---

## ⚡ How it fits together

```
trading bot (Docker)  ──►  exporter/run_export.sh  (weekdays 18:30 IST, cron)
  strategy code, 30m index data      │  1. Nifty 50 daily closes from the market database (benchmark)
                                     │  2. exporter/export_model.py inside the bot container:
                                     │       backtest each strategy on the indices themselves,
                                     │       mark daily, combine, apply the 30-day cut-off
                                     ▼  3. exporter/split_bundle.py → data/live/*.json
showcase (FastAPI, this repo) reads data/live/*.json (mounted read-only); nothing is hard-coded
```

- **Backend:** Python 3.11, FastAPI, Uvicorn, Jinja2 (`db.py` reads the exported JSON and runs the simulator)
- **Frontend:** Tailwind CSS, Chart.js
- **Deploy:** Docker Compose (`compose.prod.yml`) behind a Caddy reverse proxy

---

## 🚀 Run locally

```bash
git clone https://github.com/shubhamsinha1107/quant-momentum-showcase.git
cd quant-momentum-showcase
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The app needs the exported files in `data/live/`; they are produced by the exporter and are not committed. Point it at a copy with `QS_DATA_DIR`:

```bash
QS_DATA_DIR=/path/to/live python -m unittest discover -s tests -v   # checks the simulator reproduces the export
QS_DATA_DIR=/path/to/live python main.py                              # http://localhost:8000
```

Without data, the tests are skipped and `/health` reports `no-data`.

---

## 👤 About the author

**Shubham Sinha**
*Investment Analyst | Portfolio Analytics & Quantitative Research*
New Delhi, India

- **LinkedIn:** [https://www.linkedin.com/in/shubham-sinha-7a3285300](https://www.linkedin.com/in/shubham-sinha-7a3285300)
- **GitHub:** [https://github.com/shubhamsinha1107](https://github.com/shubhamsinha1107)
- **Background:** manages portfolio risk and quantitative analytics across an INR 400+ Cr single family office & conglomerate portfolio (equities, mutual funds, precious metals, and unlisted holdings).
