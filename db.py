"""
db.py - Data access for the showcase.

All numbers come from the files the exporter writes (exporter/run_export.sh) into DATA_DIR:
the 4 Horse STAT strategies traded on the sector indices / ETFs themselves, published with a delay.
Nothing here is hard-coded; if the files are missing the API says so instead of inventing data.
"""
import json
import math
import os
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

DATA_DIR = Path(os.getenv("QS_DATA_DIR", Path(__file__).resolve().parent / "data" / "live"))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_cache: Dict[str, Tuple[float, Any]] = {}


def _load(name: str, default: Any) -> Any:
    """Read DATA_DIR/<name>.json, re-reading only when the file changes."""
    p = DATA_DIR / f"{name}.json"
    try:
        mtime = p.stat().st_mtime
    except OSError:
        return default
    hit = _cache.get(name)
    if hit and hit[0] == mtime:
        return hit[1]
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    _cache[name] = (mtime, data)
    return data


REPO_DATA = Path(__file__).resolve().parent / "data"


def get_cv_snapshot() -> Dict[str, Any]:
    """Fixed-period figures quoted on the CV (data/cv_snapshot.json, frozen by tools/make_cv_snapshot.py)."""
    p = REPO_DATA / "cv_snapshot.json"
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def get_meta() -> Dict[str, Any]:
    return _load("meta", {})


def get_summary_metrics() -> List[Dict[str, Any]]:
    return _load("summary_metrics", [])


def get_index_metrics() -> List[Dict[str, Any]]:
    return _load("index_metrics", [])


def get_annual_returns() -> List[Dict[str, Any]]:
    return _load("annual_returns", [])


def get_monthly_matrix() -> List[Dict[str, Any]]:
    return _load("monthly_matrix", [])


def get_equity_series() -> Dict[str, Any]:
    return _load("equity_series", {"dates": [], "master_nav": [], "benchmark_nav": [], "drawdown": []})


def _sim_data() -> Dict[str, Any]:
    return _load("sim", {})


def get_trades(limit: int = 50, offset: int = 0, index_sym: Optional[str] = None,
               sleeve: Optional[str] = None, newest_first: bool = True) -> Tuple[List[Dict[str, Any]], int]:
    trades = _load("trades", [])
    if index_sym and index_sym.strip() and index_sym.strip().lower() != "all":
        q = index_sym.strip().upper()
        trades = [t for t in trades if q in (t.get("Stock", "").upper(), t.get("Index", "").upper())]
    if sleeve and sleeve.strip() and sleeve.strip().lower() != "all":
        q = sleeve.strip().lower()
        trades = [t for t in trades if q in t.get("Sleeve", "").lower()]
    if newest_first:
        trades = trades[::-1]
    return trades[offset:offset + limit], len(trades)


def get_universe() -> List[Dict[str, str]]:
    """Indices / ETFs that appear in the trades, with their display names."""
    names = {}
    for t in _load("trades", []):
        names[t["Stock"]] = t.get("Index", t["Stock"])
    return [{"sym": k, "name": v} for k, v in sorted(names.items(), key=lambda kv: kv[1])]


# ── statistics (same definitions as the exporter) ─────────────────────────────
def _stats(dates: List[str], eq: List[float]) -> Dict[str, float]:
    """eq is the value at each day's close, starting from 1.0 before the first day."""
    from datetime import date
    rets = [eq[0] - 1.0] + [eq[i] / eq[i - 1] - 1.0 for i in range(1, len(eq))]
    d0, d1 = date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
    yrs = (d1 - d0).days / 365.25
    total = eq[-1] - 1.0
    cagr = eq[-1] ** (1 / yrs) - 1 if yrs > 0 and eq[-1] > 0 else 0.0
    peak, mdd = 1.0, 0.0
    for v in eq:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    n = len(rets)
    mean = sum(rets) / n
    sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / (n - 1)) if n > 1 else 0.0
    down = math.sqrt(sum(min(r, 0.0) ** 2 for r in rets) / n)
    return {
        "total_return": round(total * 100, 1), "cagr": round(cagr * 100, 1), "max_dd": round(mdd * 100, 1),
        "volatility": round(sd * math.sqrt(252) * 100, 1),
        "sharpe": round(mean / sd * math.sqrt(252), 2) if sd > 0 else 0.0,
        "sortino": round(mean / down * math.sqrt(252), 2) if down > 0 else 0.0,
        "calmar": round(cagr / abs(mdd), 2) if mdd < 0 else 0.0,
    }


def _trade_stats(net: Iterable[float]) -> Dict[str, float]:
    n = list(net)
    if not n:
        return {"trades": 0, "win_rate": 0.0, "avg_trade_pct": 0.0, "profit_factor": 0.0}
    pos, neg = sum(x for x in n if x > 0), -sum(x for x in n if x < 0)
    return {"trades": len(n), "win_rate": round(100 * sum(x > 0 for x in n) / len(n), 1),
            "avg_trade_pct": round(100 * sum(n) / len(n), 2),
            "profit_factor": round(pos / neg, 2) if neg > 0 else 0.0}


def _calendar(dates: List[str], eq: List[float], bench: List[float]):
    """Monthly matrix and calendar-year returns from a daily equity curve."""
    month_end, year_end, b_year_end = {}, {}, {}
    for d, v, b in zip(dates, eq, bench):
        month_end[d[:7]] = v
        year_end[d[:4]] = v
        b_year_end[d[:4]] = b
    monthly, annual = [], []
    prev_m, prev_y, prev_b = 1.0, 1.0, 1.0
    for y in sorted(year_end):
        row = {"year": int(y)}
        for i, m in enumerate(MONTHS, 1):
            k = f"{y}-{i:02d}"
            if k in month_end:
                row[m] = round((month_end[k] / prev_m - 1) * 100, 1)
                prev_m = month_end[k]
            else:
                row[m] = None
        yr = year_end[y] / prev_y - 1
        row["total"] = row["Total"] = round(yr * 100, 1)
        monthly.append(row)
        annual.append({"year": y, "strategy": round(yr * 100, 1),
                       "benchmark": round((b_year_end[y] / prev_b - 1) * 100, 1)})
        prev_y, prev_b = year_end[y], b_year_end[y]
    return monthly, annual


# ── simulator ────────────────────────────────────────────────────────────────
def simulate_portfolio(strategies: Optional[List[str]] = None, universe: Optional[List[str]] = None,
                       cost_rt_pct: Optional[float] = None, monthly_stop: Optional[float] = None,
                       end: Optional[str] = None) -> Dict[str, Any]:
    """
    Re-runs the published model on its own trades with your choices:
      strategies    which strategies to include (their weights are rescaled to 100%)
      universe      which indices / ETFs may be traded; a trade in an excluded one is skipped and that
                    strategy sits in cash for that period (it does NOT get the next-ranked index instead)
      cost_rt_pct   round-trip cost per trade in % (half on the entry day, half on the exit day)
      monthly_stop  e.g. -5: once the portfolio is down 5% or more for the calendar month at a day's
                    close, no new trades open for the rest of that month (open trades run to their exit).
                    Uses only closes up to the day before an entry, so there is no look-ahead.
      end           "YYYY-MM-DD": stop the run at that date (open trades are valued at that day's close
                    and don't count as closed trades), e.g. for a fixed period quoted elsewhere.
    Equity is marked to market daily and rebalanced to the target weights each month, exactly as the
    exporter does, so the default settings reproduce the published numbers.
    """
    sim, meta = _sim_data(), get_meta()
    if not sim:
        return {"error": "no data exported yet"}
    if end:
        n = sum(1 for d in sim["dates"] if d <= end)
        if n < 2:
            return {"error": "end date is before the data starts"}
        cut = []
        for si, sym, closed_exit, path in sim["trades"]:
            p = [x for x in path if x[0] < n]
            if p:
                cut.append([si, sym, closed_exit if len(p) == len(path) else 0, p])
        sim = {**sim, "dates": sim["dates"][:n], "benchmark": sim["benchmark"][:n], "trades": cut}
    dates, bench = sim["dates"], sim["benchmark"]
    sl = sim["sleeves"]
    ids = [s["id"] for s in sl]
    chosen = [i for i, s in enumerate(sl) if not strategies or s["id"] in strategies]
    if not chosen:
        return {"error": "pick at least one strategy"}
    allowed = {u.upper() for u in universe} if universe else None
    cost = meta.get("cost_round_trip_pct", 0.20) if cost_rt_pct is None else max(0.0, min(float(cost_rt_pct), 2.0))
    half = cost / 200.0
    tot_w = sum(sl[i]["weight"] for i in chosen)
    tgt = {i: sl[i]["weight"] / tot_w for i in chosen}
    reb_cost = float(sim.get("rebalance_cost_pct", 0.30)) / 100.0
    n_days = len(dates)

    # trades by entry day
    starts = defaultdict(list)
    for k, (si, sym, closed_exit, path) in enumerate(sim["trades"]):
        if si in tgt and (allowed is None or sym in allowed) and path:
            starts[path[0][0]].append(k)

    day_ret = {i: defaultdict(list) for i in chosen}   # sleeve -> day -> [returns of trades that day]
    taken, skipped_stop = [], 0
    w = dict(tgt)
    v, eq = 1.0, []
    month_start_v, cur_month = 1.0, None
    halted = False
    active_days = 0
    for d in range(n_days):
        m = dates[d][:7]
        if m != cur_month:
            if cur_month is not None:
                moved = sum(abs(w[i] - tgt[i]) for i in chosen) / 2
                v *= 1 - reb_cost * moved
                w = dict(tgt)
            cur_month, month_start_v, halted = m, v, False
        for k in starts.get(d, ()):
            if halted:
                skipped_stop += 1
                continue
            si, sym, closed_exit, path = sim["trades"][k]
            last = len(path) - 1
            for j, (dd, r) in enumerate(path):
                if j == 0:
                    r = (1 + r) * (1 - half) - 1
                if j == last and closed_exit:
                    r = (1 + r) * (1 - half) - 1
                day_ret[si][dd].append(r)
            taken.append(k)
        g = {}
        for i in chosen:
            rs = day_ret[i].get(d)
            r = 1.0
            for x in rs or ():
                r *= 1 + x            # one position at a time: same-day trades follow each other
            g[i] = w[i] * r
        if any(g[i] != w[i] for i in chosen):
            active_days += 1
        tot = sum(g.values()) + (1 - sum(w.values()))
        v *= tot
        w = {i: g[i] / tot for i in chosen}
        eq.append(v)
        if monthly_stop is not None and monthly_stop < 0 and v / month_start_v - 1 <= monthly_stop / 100.0:
            halted = True   # applies from the next day's entries

    # trade list (closed trades only)
    net, rows = [], []
    for k in taken:
        si, sym, closed_exit, path = sim["trades"][k]
        if not closed_exit:
            continue
        gross = 1.0
        for _, r in path:
            gross *= 1 + r
        n = gross * (1 - half) ** 2 - 1
        net.append(n)
        rows.append({"sym": sym, "strategy": sl[si]["name"], "entry": dates[path[0][0]],
                     "exit": dates[path[-1][0]], "ret": round(n * 100, 2)})
    rows.sort(key=lambda r: (r["exit"], r["sym"]))

    bench_eq = [b / bench[0] for b in bench]
    out = {**_stats(dates, eq), **_trade_stats(net)}
    out["benchmark"] = _stats(dates, bench_eq)
    out["exposure_pct"] = round(100 * active_days / n_days, 1)
    monthly, annual = _calendar(dates, eq, bench_eq)

    # weekly points for the charts (+ the last day)
    pts, seen = [], set()
    from datetime import date
    for idx, d in enumerate(dates):
        wk = date.fromisoformat(d).isocalendar()[:2]
        if idx + 1 == n_days or date.fromisoformat(dates[idx + 1]).isocalendar()[:2] != wk:
            pts.append(idx)
    peak, dd_series = 1.0, []
    for x in eq:
        peak = max(peak, x)
        dd_series.append(x / peak - 1)
    out.update({
        "settings": {"strategies": [ids[i] for i in chosen], "universe": sorted(allowed) if allowed else "all",
                     "cost_rt_pct": cost, "monthly_stop": monthly_stop,
                     "weights": {sl[i]["name"]: round(tgt[i] * 100, 1) for i in chosen}},
        "skipped_by_stop": skipped_stop,
        "final_nav": round(eq[-1] * 100, 2),
        "dates": [dates[i] for i in pts],
        "nav_series": [round(eq[i] * 100, 2) for i in pts],
        "benchmark_nav": [round(bench_eq[i] * 100, 2) for i in pts],
        "dd_series": [round(dd_series[i] * 100, 2) for i in pts],
        "monthly_matrix": monthly, "annual": annual,
        "recent_trades": rows[-15:][::-1],
        "cutoff": dates[-1],
    })
    return out
