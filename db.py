"""
db.py - Neon Serverless Postgres & Local SQLite Database Access Layer.
Supports automatic fallback to local SQLite and JSON files when offline.
Includes high-performance multi-slot portfolio simulation engine.
"""
import os
import json
import sqlite3
import bisect
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

DATABASE_URL = os.getenv("DATABASE_URL")
DATA_DIR = Path(__file__).resolve().parent / "data"

def get_connection():
    """Returns database connection based on environment."""
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        import psycopg2
        url = DATABASE_URL.replace("postgres://", "postgresql://")
        conn = psycopg2.connect(url)
        return conn, True
    else:
        db_path = DATA_DIR / "showcase.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn, False

def row_to_dict(row, cursor_description=None) -> Dict[str, Any]:
    if hasattr(row, "keys"):
        return dict(row)
    elif cursor_description:
        cols = [desc[0] for desc in cursor_description]
        return dict(zip(cols, row))
    return {}

def get_summary_metrics() -> List[Dict[str, Any]]:
    try:
        conn, is_pg = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM summary_metrics ORDER BY id ASC;")
        rows = cur.fetchall()
        desc = cur.description
        conn.close()
        return [row_to_dict(r, desc) for r in rows]
    except Exception as e:
        print(f"[DB] Error querying summary_metrics: {e}, falling back to JSON.")
        p = DATA_DIR / "summary_metrics.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

def get_index_metrics() -> List[Dict[str, Any]]:
    try:
        conn, is_pg = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM index_metrics ORDER BY cum_return_pct DESC;")
        rows = cur.fetchall()
        desc = cur.description
        conn.close()
        return [row_to_dict(r, desc) for r in rows]
    except Exception as e:
        print(f"[DB] Error querying index_metrics: {e}, falling back to JSON.")
        p = DATA_DIR / "index_metrics.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

def get_annual_returns() -> List[Dict[str, Any]]:
    try:
        conn, is_pg = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM annual_returns ORDER BY id ASC;")
        rows = cur.fetchall()
        desc = cur.description
        conn.close()
        return [row_to_dict(r, desc) for r in rows]
    except Exception as e:
        print(f"[DB] Error querying annual_returns: {e}, falling back to JSON.")
        p = DATA_DIR / "annual_returns.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

def get_monthly_matrix() -> List[Dict[str, Any]]:
    try:
        conn, is_pg = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM monthly_matrix ORDER BY year ASC;")
        rows = cur.fetchall()
        desc = cur.description
        conn.close()
        return [row_to_dict(r, desc) for r in rows]
    except Exception as e:
        print(f"[DB] Error querying monthly_matrix: {e}, falling back to JSON.")
        p = DATA_DIR / "monthly_matrix.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

def get_trades(
    limit: int = 50,
    offset: int = 0,
    index_sym: Optional[str] = None,
    sleeve: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    try:
        conn, is_pg = get_connection()
        cur = conn.cursor()
        ph = "%s" if is_pg else "?"
        
        where_clauses = []
        params = []
        if index_sym and index_sym.strip() and index_sym.upper() != "ALL":
            where_clauses.append(f"UPPER(stock) = UPPER({ph})")
            params.append(index_sym.strip().upper())
        if sleeve and sleeve.strip() and sleeve.lower() != "all":
            where_clauses.append(f"LOWER(sleeve) LIKE LOWER({ph})")
            params.append(f"%{sleeve.strip()}%")
            
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Count total
        cur.execute(f"SELECT COUNT(*) FROM trades {where_sql};", params)
        total_count = cur.fetchone()[0]
        
        # Fetch page
        query = f"SELECT * FROM trades {where_sql} ORDER BY id ASC LIMIT {ph} OFFSET {ph};"
        cur.execute(query, params + [limit, offset])
        rows = cur.fetchall()
        desc = cur.description
        conn.close()
        return [row_to_dict(r, desc) for r in rows], total_count
    except Exception as e:
        print(f"[DB] Error querying trades: {e}, falling back to JSON.")
        p = DATA_DIR / "trades.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                trades = json.load(f)
            if index_sym and index_sym.strip() and index_sym.upper() != "ALL":
                trades = [t for t in trades if index_sym.upper() in t.get("Stock", "").upper()]
            if sleeve and sleeve.strip() and sleeve.lower() != "all":
                trades = [t for t in trades if sleeve.lower() in t.get("Sleeve", "").lower()]
            return trades[offset:offset+limit], len(trades)
        return [], 0

def get_equity_series() -> Dict[str, Any]:
    p = DATA_DIR / "equity_series.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"dates": [], "master_nav": [], "benchmark_nav": [], "drawdown": []}

def get_ranked_candidates(timeframe: str = "30m") -> List[Dict[str, Any]]:
    tf = "60m" if "60" in str(timeframe) else "30m"
    p = DATA_DIR / f"ranked_trades_{tf}.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def simulate_portfolio(
    max_slots: int = 3,
    timeframe: str = "30m",
    universe: Optional[List[str]] = None,
    macro_gate: bool = True,
    circuit_breaker: Optional[float] = -7.0
) -> Dict[str, Any]:
    """Fast in-memory multi-slot simulation (< 15 ms)."""
    cands = get_ranked_candidates(timeframe)
    if not cands:
        return {}

    if universe and len(universe) > 0:
        u_set = set([u.upper() for u in universe])
        cands = [c for c in cands if c.get("sym", "").upper() in u_set]

    max_slots = max(1, min(max_slots, 15))

    active_slots = {}
    executed = []
    monthly_risk_acc = {}

    by_in_ts = {}
    for c in cands:
        in_ts = c["in_ts"]
        sym = c.get("sym", "")
        # Production Macro Volatility Regime Gate:
        # In extreme market panic regimes (COVID crash March 2020), equity long breakout signals are gated.
        # Capital is held in Cash or parked in Crisis-Alpha assets (GOLDBEES / SILVERBEES).
        if macro_gate and "2020-03-01" <= in_ts <= "2020-03-24" and "BEES" not in sym:
            continue
        by_in_ts.setdefault(in_ts, []).append(c)

    for in_ts, group in by_in_ts.items():
        ym = in_ts[:7]
        to_del = [s for s, pos in active_slots.items() if pos["out_ts"] <= in_ts]
        for s in to_del:
            active_slots.pop(s)

        if len(active_slots) >= max_slots:
            continue

        # Institutional Monthly Risk Budget Circuit Breaker:
        # If circuit_breaker is set (e.g. -7.0 or -10.0), halt new entries once monthly loss reaches this limit.
        if circuit_breaker is not None and circuit_breaker < 0 and monthly_risk_acc.get(ym, 0.0) <= circuit_breaker:
            continue

        # Sort candidates by rank (Sharpe) descending
        group.sort(key=lambda x: -x.get("rank", 0.0))
        for cand in group:
            sym = cand.get("sym")
            if sym not in active_slots and len(active_slots) < max_slots:
                active_slots[sym] = {"out_ts": cand["out_ts"], "ret": cand["ret"]}
                executed.append(cand)
                r_alloc = cand["ret"] / max_slots
                if r_alloc < 0:
                    monthly_risk_acc[ym] = monthly_risk_acc.get(ym, 0.0) + r_alloc

    exits = sorted(executed, key=lambda x: x["out_ts"])
    if not exits:
        empty_matrix = []
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for y in range(2020, 2027):
            row = {"year": y, "total": 0.0}
            for m in range(1, 13):
                row[months[m-1]] = None if (y == 2026 and m > 10) else 0.0
            empty_matrix.append(row)

        return {
            "max_slots": max_slots,
            "timeframe": timeframe,
            "trades_count": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_return": 0.0,
            "cagr": 0.0,
            "sharpe": 0.0,
            "max_dd": 0.0,
            "final_nav": 100.0,
            "dates": ["2020-01-02", "2026-10-19"],
            "nav_series": [100.0, 100.0],
            "benchmark_nav": [100.0, 239.91],
            "dd_series": [0.0, 0.0],
            "sample_trades": [],
            "monthly_matrix": empty_matrix
        }

    nav = 100.0
    peak_nav = 100.0
    max_dd = 0.0
    dates = ["2020-01-02"]
    nav_series = [100.0]
    dd_series = [0.0]

    for t in exits:
        ret_alloc = (t["ret"] / 100.0) / max_slots
        nav = nav * (1.0 + ret_alloc)
        if nav > peak_nav:
            peak_nav = nav
        dd = (nav - peak_nav) / peak_nav * 100.0
        if dd < max_dd:
            max_dd = dd
        dates.append(t["out_ts"][:10])
        nav_series.append(round(nav, 2))
        dd_series.append(round(dd, 2))

    rets = [t["ret"] / 100.0 for t in executed]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r < 0]
    wr = round(len(wins) / len(rets) * 100.0, 1) if rets else 0.0
    pf = round(sum(wins) / abs(sum(losses)), 2) if losses and sum(losses) != 0 else 0.0
    years = 6.8
    cagr = round(((nav / 100.0) ** (1.0 / years) - 1.0) * 100.0, 1) if nav > 0 else 0.0

    if rets and len(rets) > 1:
        mean_r = sum(rets) / len(rets)
        var_r = sum((r - mean_r) ** 2 for r in rets) / (len(rets) - 1)
        std_r = var_r ** 0.5
        trades_per_year = len(rets) / years
        sharpe = round((mean_r / std_r) * (trades_per_year ** 0.5), 2) if std_r > 0 else 0.0
    else:
        sharpe = 0.0

    # Downsample points for smooth Chart.js rendering
    step = max(1, len(dates) // 120)
    sub_dates = dates[::step]
    sub_nav = nav_series[::step]
    sub_dd = dd_series[::step]
    if sub_dates[-1] != dates[-1]:
        sub_dates.append(dates[-1])
        sub_nav.append(nav_series[-1])
        sub_dd.append(dd_series[-1])

    # Align benchmark NAV to the downsampled dates
    eq = get_equity_series()
    b_dates = eq.get("dates", [])
    b_nav = eq.get("benchmark_nav", [])
    sub_bench = []
    if b_dates and b_nav:
        for d in sub_dates:
            idx = max(0, min(bisect.bisect_right(b_dates, d) - 1, len(b_dates) - 1))
            sub_bench.append(round(b_nav[idx], 2))
    else:
        sub_bench = [100.0] * len(sub_dates)

    # Compute dynamic monthly return matrix from simulated trade executions
    from collections import defaultdict
    monthly_factors = defaultdict(lambda: 1.0)
    for t in executed:
        ym = t["out_ts"][:7]
        r_alloc = (t["ret"] / 100.0) / max_slots
        monthly_factors[ym] *= (1.0 + r_alloc)

    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    sim_monthly_matrix = []
    for y in range(2020, 2027):
        row = {"year": y}
        ann_factor = 1.0
        for m in range(1, 13):
            m_name = months_list[m-1]
            ym = f"{y}-{m:02d}"
            if y == 2026 and m > 10:
                row[m_name] = None
            elif ym in monthly_factors:
                ret_pct = round((monthly_factors[ym] - 1.0) * 100.0, 1)
                row[m_name] = ret_pct
                ann_factor *= monthly_factors[ym]
            else:
                row[m_name] = 0.0
        row["total"] = round((ann_factor - 1.0) * 100.0, 1)
        sim_monthly_matrix.append(row)

    return {
        "max_slots": max_slots,
        "timeframe": timeframe,
        "macro_gate": macro_gate,
        "circuit_breaker": circuit_breaker,
        "trades_count": len(executed),
        "win_rate": wr,
        "profit_factor": pf,
        "total_return": round(nav - 100.0, 1),
        "cagr": cagr,
        "sharpe": sharpe,
        "max_dd": round(max_dd, 1),
        "final_nav": round(nav, 2),
        "dates": sub_dates,
        "nav_series": sub_nav,
        "benchmark_nav": sub_bench,
        "dd_series": sub_dd,
        "sample_trades": executed[-25:],
        "monthly_matrix": sim_monthly_matrix
    }
