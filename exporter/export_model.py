"""
Showcase export: the 4 Horse STAT strategies run on the sector indices / ETFs themselves
(mode="direct_index", no proxy stocks), published with a delay.

Runs inside horse_apocalypse_container:  python - < export_model.py
Writes one JSON bundle to /tmp/qs_bundle.json (the host script splits it into the showcase's files).

Accounting
  * Each strategy (sleeve) holds the index it trades from the entry bar's close to the exit bar's close.
    Its equity is marked to market every day on the index's daily close (last 30m bar of the day),
    so drawdowns include open-trade losses, not just closed trades.
  * Costs: COST_RT_PCT round trip (half charged on the entry day, half on the exit day).
  * Portfolio: sleeves at their config.yaml weights (renormalised over the sleeves included here),
    rebalanced monthly with the dashboard model's own combine() and rebalance cost.
  * Delay: only data up to CUTOFF = today - LAG_DAYS. Trades that closed after the cutoff are not shown;
    a trade still open at the cutoff counts in the equity curve up to the cutoff only.
  * Sharpe / Sortino on daily returns x sqrt(252), risk-free rate 0. Benchmark: Nifty 50 price index.
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, "/app")
import config_loader as cfg  # noqa: E402
from _run_stat_sectoral_backtest import backtest_stat_sectoral_proxy  # noqa: E402
from strategies import model_costs as mc  # noqa: E402
from data_cache import market_cache  # noqa: E402

LAG_DAYS = int(os.environ.get("QS_LAG_DAYS", "30"))
COST_RT_PCT = float(os.environ.get("QS_COST_RT_PCT", "0.20"))
START = "2020-01-01"
NIFTY_CSV = "/tmp/qs_nifty.csv"
OUT = "/tmp/qs_bundle.json"

NAMES = {
    "STAT_RAPID_30_ALL": "Rapid Sector Momentum",
    "STAT_CORE_20_U3": "Core Sector Momentum",
    "STAT_HEDGE_20_U1": "Multi-Asset Hedge",
    "STAT_SAT_30_MS50": "Midcap Satellite",
}
PRETTY = {
    "FINNIFTY": "Nifty Financial Services", "GOLDBEES": "Gold ETF (GOLDBEES)", "SILVERBEES": "Silver ETF (SILVERBEES)",
    "NIFTYAUTO": "Nifty Auto", "NIFTYBANK": "Nifty Bank", "NIFTYCAPITALMKT": "Nifty Capital Markets",
    "NIFTYENERGY": "Nifty Energy", "NIFTYHEALTHCARE": "Nifty Healthcare", "NIFTYINDDEFENCE": "Nifty India Defence",
    "NIFTYIT": "Nifty IT", "NIFTYMETAL": "Nifty Metal", "NIFTYMIDCAP150": "Nifty Midcap 150",
    "NIFTYMIDCAP50": "Nifty Midcap 50", "NIFTYPSUBANK": "Nifty PSU Bank", "NIFTYREALTY": "Nifty Realty",
    "NIFTYSMLCAP250": "Nifty Smallcap 250", "NIFTYSMLCAP50": "Nifty Smallcap 50",
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

half = COST_RT_PCT / 200.0
today = pd.Timestamp.now().normalize()
cutoff = today - pd.Timedelta(days=LAG_DAYS)
cut_end = cutoff + pd.Timedelta(days=1)  # exclusive: everything on the cutoff day counts

snap = market_cache.get()
close30 = snap.close_df.loc[START:]
daily = close30.groupby(close30.index.normalize()).last()
days = daily.index[daily.index <= cutoff]
if len(days) < 250:
    raise SystemExit(f"too little price history before the cutoff ({len(days)} days)")
last_day = days[-1]


def sym_of(x):
    return str(x).upper().replace("-INDEX", "").replace("NSE:", "").strip()


def trade_path(sym, tin, pin, tout, pout, closed):
    """Daily returns of one trade on the daily-close grid, up to the cutoff. Costs included."""
    c = daily[sym]
    din, dout = tin.normalize(), tout.normalize()
    upto = min(dout, last_day)
    out, prev = {}, pin
    grid = c.index[(c.index >= din) & (c.index <= upto)]
    for d in grid:
        px = pout if (closed and d == dout) else c.loc[d]
        if pd.isna(px):
            continue
        r = px / prev - 1.0
        prev = px
        if d == din:
            r = (1 + r) * (1 - half) - 1
        if closed and d == dout:
            r = (1 + r) * (1 - half) - 1
        out[d] = r
    return out


ms = mc.settings()
act = cfg.Strategies.active_strategies()
sleeves = [s for s, d in act.items()
           if str(d.get("type", "")).startswith("stat_") and float(d.get("cash_allocation_pct", 0) or 0) > 0]
raw_w = {s: float(act[s]["cash_allocation_pct"]) for s in sleeves}
tot_w = sum(raw_w.values())
weights = {s: raw_w[s] / tot_w for s in sleeves}

rets, exposure, trades, sanity, concurrency = {}, {}, [], {}, {}
sim_trades = []
day_pos = {d: i for i, d in enumerate(days)}
for s in sleeves:
    d = act[s]
    df = backtest_stat_sectoral_proxy(START, "2030-01-01", strategy_name=s, top_k=None, mode="direct_index",
                                      symbols_filter=cfg.SymbolGroups.get_group(d["symbol_group"]), use_cache=False)
    if df is None or df.empty:
        rets[s] = pd.Series(0.0, index=days)
        continue
    df = df.copy()
    df["tin"], df["tout"] = pd.to_datetime(df["Entry Time"]), pd.to_datetime(df["Exit Time"])
    df = df[df["tin"] <= cut_end].sort_values("tin")
    by_day = defaultdict(list)
    active_days = set()
    diffs = []
    for _, t in df.iterrows():
        sym = sym_of(t["Index"])
        if sym not in daily.columns:
            continue
        closed = t["tout"] < cut_end
        p = trade_path(sym, t["tin"], float(t["Entry Price"]), t["tout"], float(t["Exit Price"]), closed)
        if p:
            gp = dict(p)
            k0, k1 = min(gp), max(gp)
            gp[k0] = (1 + gp[k0]) / (1 - half) - 1
            if closed and t["tout"].normalize() == k1:
                gp[k1] = (1 + gp[k1]) / (1 - half) - 1
            sim_trades.append([sleeves.index(s), sym, int(closed and t["tout"].normalize() == k1),
                               [[day_pos[k], round(v, 7)] for k, v in sorted(gp.items())]])
        for day, r in p.items():
            by_day[day].append(r)
        active_days.update(p.keys())
        if closed:
            net = (1 + float(t["Return"])) * (1 - half) ** 2 - 1
            gross_path = np.prod([1 + r for r in p.values()]) / (1 - half) ** 2 - 1 if p else np.nan
            diffs.append(abs(gross_path - float(t["Return"])))
            trades.append({
                "sleeve_id": s, "sym": sym, "tin": t["tin"], "tout": t["tout"],
                "pin": float(t["Entry Price"]), "pout": float(t["Exit Price"]),
                "gross": float(t["Return"]), "net": net,
                "days": (t["tout"] - t["tin"]).total_seconds() / 86400.0,
            })
    # One position at a time per strategy: trades on the same day follow each other (exit, then the next
    # entry with the proceeds), so their day returns compound. Truly overlapping trades would share capital.
    spans = sorted((t["tin"], t["tout"]) for t in trades if t["sleeve_id"] == s)
    overlaps = sum(1 for a, b in zip(spans, spans[1:]) if b[0] < a[1])
    if overlaps:
        r = pd.Series({k: float(np.mean(v)) for k, v in by_day.items()})
    else:
        r = pd.Series({k: float(np.prod([1 + x for x in v]) - 1) for k, v in by_day.items()})
    r = r.reindex(days).fillna(0.0)
    rets[s] = r
    exposure[s] = len(active_days) / len(days)
    concurrency[s] = {"overlapping_trades": overlaps, "max_trades_same_day": int(max((len(v) for v in by_day.values()), default=0))}
    sanity[s] = {"closed_trades": len(diffs), "max_path_vs_engine_diff": float(np.nanmax(diffs)) if diffs else 0.0}

R = pd.DataFrame(rets, index=days).fillna(0.0)
port_eq, rebal_cost = mc.combine(R, weights, ms["rebalance"], ms["rebalance_cost_pct"])

# Benchmark: Nifty 50 daily close
nf = pd.read_csv(NIFTY_CSV, names=["day", "close"], parse_dates=["day"]).set_index("day")["close"]
nifty = nf.reindex(nf.index.union(days)).ffill().reindex(days)
nifty_eq = nifty / nifty.iloc[0]


def stats(eq, bench=None):
    eq = eq.dropna()
    r = eq.pct_change().fillna(eq.iloc[0] - 1.0)
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    total = eq.iloc[-1] - 1.0
    cagr = (eq.iloc[-1]) ** (1 / yrs) - 1 if yrs > 0 else 0.0
    dd = (eq / eq.cummax().clip(lower=1.0) - 1).min()
    sd = r.std()
    down = np.sqrt(np.mean(np.minimum(r, 0) ** 2))
    out = {
        "total_return": round(total * 100, 1), "cagr": round(cagr * 100, 1), "max_dd": round(dd * 100, 1),
        "volatility": round(sd * np.sqrt(252) * 100, 1),
        "sharpe": round(r.mean() / sd * np.sqrt(252), 2) if sd > 0 else 0.0,
        "sortino": round(r.mean() / down * np.sqrt(252), 2) if down > 0 else 0.0,
        "calmar": round(cagr / abs(dd), 2) if dd < 0 else 0.0,
    }
    if bench is not None:
        b = bench.pct_change().fillna(0.0)
        out["beta"] = round(float(np.cov(r, b)[0, 1] / np.var(b, ddof=1)), 2)
    return out


def trade_stats(ts):
    n = [t["net"] for t in ts]
    if not n:
        return {"trades": 0, "win_rate": 0.0, "avg_trade_pct": 0.0, "profit_factor": 0.0}
    pos, neg = sum(x for x in n if x > 0), -sum(x for x in n if x < 0)
    return {"trades": len(n), "win_rate": round(100 * sum(x > 0 for x in n) / len(n), 1),
            "avg_trade_pct": round(100 * float(np.mean(n)), 2),
            "profit_factor": round(pos / neg, 2) if neg > 0 else 0.0}


def universe(s):
    return ", ".join(PRETTY.get(sym_of(x), sym_of(x)) for x in cfg.SymbolGroups.get_group(act[s]["symbol_group"]))


any_active = (R != 0).any(axis=1)
master = {
    "name": "Combined Portfolio (index-level)", "type": "master", "horizon": "30m / 60m signals",
    "allocation": "100% across " + str(len(sleeves)) + " strategies",
    **trade_stats(trades), **stats(port_eq, nifty_eq),
    "exposure_pct": round(100 * float(any_active.mean()), 1),
    "asset_classes": "NSE sector & broad indices, Gold and Silver ETFs, cash",
}
master["total_trades"] = master["trades"]
summary = [master]
for i, s in enumerate(sleeves, 1):
    st = (1 + R[s]).cumprod()
    summary.append({
        "name": f"Strategy {i}: {NAMES.get(s, s)}", "type": "sleeve", "id": s,
        "horizon": "60-min" if "60" in str(act[s].get("type")) else "30-min",
        "allocation": f"{weights[s] * 100:.0f}% of capital",
        **trade_stats([t for t in trades if t["sleeve_id"] == s]), **stats(st, nifty_eq),
        "exposure_pct": round(100 * exposure.get(s, 0.0), 1),
        "asset_classes": universe(s),
    })

# Per index: standalone (trade returns compounded) and contribution to the portfolio (weight x net return)
idx_rows = []
by_sym = defaultdict(list)
for t in trades:
    by_sym[t["sym"]].append(t)
for sym, ts in by_sym.items():
    n = [t["net"] for t in ts]
    st = trade_stats(ts)
    idx_rows.append({
        "index": sym, "index_name": PRETTY.get(sym, sym), **st,
        "cum_return_pct": round((float(np.prod([1 + x for x in n])) - 1) * 100, 1),
        "standalone_return_pct": round((float(np.prod([1 + x for x in n])) - 1) * 100, 1),
        "max_win_pct": round(100 * max(n), 2), "max_loss_pct": round(100 * min(n), 2),
        "portfolio_fills": len(n), "candidate_signals": len(n),
        "portfolio_pnl_pct": round(100 * sum(weights[t["sleeve_id"]] * t["net"] for t in ts), 1),
    })
idx_rows.sort(key=lambda x: -x["cum_return_pct"])

# Yearly and monthly
frozen_through = str(ms["frozen_through"])
fy = pd.Timestamp(frozen_through).year
annual, monthly = [], []
prev = 1.0
nprev = 1.0
for y in sorted(set(days.year)):
    ye = port_eq[port_eq.index.year == y]
    ne = nifty_eq[nifty_eq.index.year == y]
    yr = ye.iloc[-1] / prev - 1
    nr = ne.iloc[-1] / nprev - 1
    sub = ye / ye.iloc[0]
    partial = y == last_day.year and last_day < pd.Timestamp(f"{y}-12-31") - pd.Timedelta(days=3)
    label = ("Out-of-sample (rules fixed end-" + str(fy) + ")") if y > fy else ("In-sample (rules developed on 2020-" + str(fy) + ")")
    if partial:
        label += f", year to {last_day:%d %b}"
    annual.append({"year": str(y), "regime": label, "simulated_return": round(yr * 100, 1),
                   "direct_baseline": round(nr * 100, 1), "benchmark_return": round(nr * 100, 1),
                   "max_dd": round(float((sub / sub.cummax() - 1).min()) * 100, 1),
                   "trades": sum(1 for t in trades if t["tout"].year == y), "partial": bool(partial),
                   "out_of_sample": y > fy})
    row = {"year": y}
    mprev = prev
    for m in range(1, 13):
        me = ye[ye.index.month == m]
        if me.empty:
            row[MONTHS[m - 1]] = None
            continue
        row[MONTHS[m - 1]] = round((me.iloc[-1] / mprev - 1) * 100, 1)
        mprev = me.iloc[-1]
    row["total"] = row["Total"] = round(yr * 100, 1)
    monthly.append(row)
    prev, nprev = ye.iloc[-1], ne.iloc[-1]

# Equity series (weekly points + last day)
dd = port_eq / port_eq.cummax().clip(lower=1.0) - 1
wk = port_eq.groupby(port_eq.index.to_period("W")).tail(1).index
if wk[-1] != port_eq.index[-1]:
    wk = wk.append(pd.DatetimeIndex([port_eq.index[-1]]))
equity = {
    "dates": [d.strftime("%Y-%m-%d") for d in wk],
    "master_nav": [round(float(port_eq.loc[d]) * 100, 2) for d in wk],
    "benchmark_nav": [round(float(nifty_eq.loc[d]) * 100, 2) for d in wk],
    "drawdown": [round(float(dd.loc[d]) * 100, 2) for d in wk],
    "benchmark_label": "Nifty 50 (price index)",
}

trade_rows = []
for i, t in enumerate(sorted(trades, key=lambda x: (x["tout"], x["sym"])), 1):
    trade_rows.append({
        "Trade No": i, "Stock": t["sym"], "Index": PRETTY.get(t["sym"], t["sym"]),
        "Entry Time": t["tin"].strftime("%Y-%m-%d %H:%M"), "Exit Time": t["tout"].strftime("%Y-%m-%d %H:%M"),
        "Entry Price": round(t["pin"], 2), "Exit Price": round(t["pout"], 2),
        "Return_Pct": round(t["net"] * 100, 2), "Gross_Pct": round(t["gross"] * 100, 2),
        "Holding Period (days)": round(t["days"], 2), "Sleeve": NAMES.get(t["sleeve_id"], t["sleeve_id"]),
    })

# For the simulator: every trade's gross daily path on the day grid (costs are applied by the simulator)
sim = {"dates": [d.strftime("%Y-%m-%d") for d in days],
       "benchmark": [round(float(v), 6) for v in nifty_eq],
       "sleeves": [{"id": s, "name": NAMES.get(s, s), "weight": round(weights[s], 6)} for s in sleeves],
       "rebalance_cost_pct": ms["rebalance_cost_pct"], "trades": sim_trades}

meta = {
    "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    "cutoff": last_day.strftime("%Y-%m-%d"), "lag_days": LAG_DAYS, "start": days[0].strftime("%Y-%m-%d"),
    "years": round((days[-1] - days[0]).days / 365.25, 2), "cost_round_trip_pct": COST_RT_PCT,
    "weights": {NAMES.get(s, s): round(w * 100, 1) for s, w in weights.items()},
    "rebalance": ms["rebalance"], "rebalance_cost_pct_per_year": rebal_cost,
    "rules_fixed_through": frozen_through,
    "benchmark": "Nifty 50 (price index)",
    "benchmark_stats": stats(nifty_eq),
    "sanity": sanity, "max_concurrent_per_strategy": concurrency,
    "excluded": "Monthly index rotation sleeve (holds stock baskets, so not index-level)",
}
bundle = {"meta": meta, "summary_metrics": summary, "index_metrics": idx_rows, "annual_returns": annual,
          "monthly_matrix": monthly, "equity_series": equity, "trades": trade_rows,
          "sim": sim}
with open(OUT, "w") as f:
    json.dump(bundle, f, default=float)
print(f"[QS] bundle written: cutoff {meta['cutoff']}, {len(trade_rows)} trades, CAGR {master['cagr']}%, "
      f"max DD {master['max_dd']}%, Sharpe {master['sharpe']}, sanity {sanity}")
os._exit(0)
