"""
Checks that the showcase reproduces the exported model and that the simulator has no look-ahead.
Run: QS_DATA_DIR=<exported data dir> python -m unittest discover -s tests
"""
import math
import sys
import time
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import db  # noqa: E402

KEYS = ["cagr", "total_return", "max_dd", "sharpe", "sortino", "volatility", "calmar",
        "trades", "win_rate", "avg_trade_pct", "profit_factor", "exposure_pct"]


class TestShowcase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = db.get_meta()
        if not cls.meta:
            raise unittest.SkipTest("no exported data in " + str(db.DATA_DIR))
        cls.master = db.get_summary_metrics()[0]
        cls.base = db.simulate_portfolio()

    def test_default_simulation_reproduces_published_numbers(self):
        for k in KEYS:
            self.assertAlmostEqual(self.base[k], self.master[k], delta=0.051, msg=k)
        self.assertEqual([(a["year"], a["strategy"]) for a in self.base["annual"]],
                         [(a["year"], a["simulated_return"]) for a in db.get_annual_returns()])

    def test_published_delay(self):
        cutoff = date.fromisoformat(self.meta["cutoff"])
        gen = date.fromisoformat(self.meta["generated_at"][:10])
        self.assertGreaterEqual((gen - cutoff).days, self.meta["lag_days"])
        self.assertLessEqual((gen - cutoff).days, self.meta["lag_days"] + 5)
        trades, _ = db.get_trades(limit=100000)
        self.assertTrue(all(t["Exit Time"][:10] <= self.meta["cutoff"] for t in trades))
        self.assertLessEqual(db.get_equity_series()["dates"][-1], self.meta["cutoff"])

    def test_trades_are_index_level_and_ordered(self):
        names = {u["sym"] for u in db.get_universe()}
        self.assertTrue(names and all(s.startswith(("NIFTY", "FINNIFTY")) or s.endswith("BEES") for s in names))
        for t in db.get_trades(limit=100000)[0]:
            self.assertLess(t["Entry Time"], t["Exit Time"])
            gross = t["Exit Price"] / t["Entry Price"] - 1
            self.assertAlmostEqual(t["Gross_Pct"], gross * 100, delta=0.02)

    def test_monthly_compounds_to_final_nav(self):
        f = 1.0
        for row in self.base["monthly_matrix"]:
            f *= 1 + row["total"] / 100
        self.assertLess(abs(f * 100 - self.base["final_nav"]) / self.base["final_nav"], 0.01)

    def test_higher_cost_lowers_return(self):
        hi = db.simulate_portfolio(cost_rt_pct=0.6)
        self.assertLess(hi["cagr"], self.base["cagr"])
        self.assertEqual(hi["trades"], self.base["trades"])

    def test_monthly_stop_uses_only_past_closes(self):
        r = db.simulate_portfolio(monthly_stop=-3)
        self.assertGreater(r["skipped_by_stop"], 0)
        # A stop can only remove trades; months before any stop is hit are identical.
        self.assertLessEqual(r["trades"], self.base["trades"])
        first = next(i for i, (a, b) in enumerate(zip(r["monthly_matrix"], self.base["monthly_matrix"])) if a != b)
        self.assertGreaterEqual(first, 0)

    def test_universe_filter(self):
        r = db.simulate_portfolio(universe=["GOLDBEES", "SILVERBEES"])
        trades = [t for t in db.get_trades(limit=100000)[0] if t["Stock"] in ("GOLDBEES", "SILVERBEES")]
        self.assertEqual(r["trades"], len(trades))

    def test_single_strategy_matches_its_row(self):
        for s in db.get_summary_metrics()[1:]:
            r = db.simulate_portfolio(strategies=[s["id"]])
            for k in ("cagr", "max_dd", "sharpe", "trades"):
                self.assertAlmostEqual(r[k], s[k], delta=0.051, msg=f"{s['id']} {k}")

    def test_fast(self):
        t0 = time.time()
        for _ in range(5):
            db.simulate_portfolio(monthly_stop=-5)
        self.assertLess((time.time() - t0) / 5, 0.5)


if __name__ == "__main__":
    unittest.main()
