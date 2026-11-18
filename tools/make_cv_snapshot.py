"""
Freeze the figures quoted on the CV for a fixed period, so they never move while the live page rolls on.
Run once (or deliberately to re-freeze):  QS_DATA_DIR=data/live python tools/make_cv_snapshot.py 2026-09-30
Writes data/cv_snapshot.json (committed to the repo; the nightly export never touches it).
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import db  # noqa: E402

END = sys.argv[1] if len(sys.argv) > 1 else "2026-09-30"
KEYS = ["total_return", "cagr", "max_dd", "volatility", "sharpe", "sortino", "calmar",
        "trades", "win_rate", "avg_trade_pct", "profit_factor", "exposure_pct"]

meta = db.get_meta()
if not meta or meta["cutoff"] < END:
    raise SystemExit(f"published data ({meta.get('cutoff')}) does not reach {END} yet")
full = db.simulate_portfolio(end=END)
universe = [u["sym"] for u in db.get_universe()]
no_silver = db.simulate_portfolio(end=END, universe=[s for s in universe if s != "SILVERBEES"])
no_metals = db.simulate_portfolio(end=END, universe=[s for s in universe if s not in ("SILVERBEES", "GOLDBEES")])

snap = {
    "label": "Figures quoted on my CV",
    "start": meta["start"], "end": full["cutoff"],
    "frozen_on": datetime.now().strftime("%Y-%m-%d"),
    "definition": (f"Backtest, index-level (NSE indices + Gold/Silver ETFs, no single stocks), "
                   f"net of {meta['cost_round_trip_pct']:.2f}% round-trip cost, before tax; "
                   f"rules fixed {meta['rules_fixed_through']}."),
    "strategy": {k: full[k] for k in KEYS},
    "benchmark": {"name": meta["benchmark"], **full["benchmark"]},
    "without_silver": {k: no_silver[k] for k in ("cagr", "max_dd", "sharpe", "total_return")},
    "without_metals": {k: no_metals[k] for k in ("cagr", "max_dd", "sharpe", "total_return")},
    "annual": full["annual"],
    "weights": full["settings"]["weights"],
}
out = Path(__file__).resolve().parent.parent / "data" / "cv_snapshot.json"
out.write_text(json.dumps(snap, indent=2))
s, b = snap["strategy"], snap["benchmark"]
print(f"frozen {snap['start']} -> {snap['end']}: CAGR {s['cagr']}%, max DD {s['max_dd']}%, Sharpe {s['sharpe']}, "
      f"{s['trades']} trades | Nifty {b['cagr']}% / {b['max_dd']}% | ex-silver {snap['without_silver']['cagr']}% "
      f"/ {snap['without_silver']['max_dd']}%")
