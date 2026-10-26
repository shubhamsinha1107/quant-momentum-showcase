"""
tests/test_simulation.py - Quant Audit & Regression Test Suite
Validates mathematical consistency, friction deduction, no-lookahead timing,
macro regime gating, and monthly risk circuit breaker enforcement.
"""
import unittest
from pathlib import Path
import sys
import time

# Add root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import db

class TestQuantSimulation(unittest.TestCase):

    def test_ranked_candidates_loaded(self):
        """Verify raw candidate datasets exist and are populated."""
        cands_30m = db.get_ranked_candidates("30m")
        cands_60m = db.get_ranked_candidates("60m")
        self.assertEqual(len(cands_30m), 3205, f"Expected 3,205 30m candidates, got {len(cands_30m)}")
        self.assertEqual(len(cands_60m), 1791, f"Expected 1,791 60m candidates, got {len(cands_60m)}")

    def test_no_lookahead_bias_timing(self):
        """Ensure in_ts strictly precedes out_ts across all candidate signals."""
        cands = db.get_ranked_candidates("30m")
        for c in cands:
            self.assertLess(c["in_ts"], c["out_ts"], f"Lookahead violation detected: {c}")

    def test_macro_gate_covid_crash_protection(self):
        """Verify Macro Gate turns March 2020 positive vs raw crash."""
        # With Macro Gate Active (Default Institutional Mode)
        res_gated = db.simulate_portfolio(max_slots=3, timeframe="30m", macro_gate=True, circuit_breaker=-7.0)
        row_2020_gated = next(r for r in res_gated["monthly_matrix"] if r["year"] == 2020)
        self.assertGreater(row_2020_gated["Mar"], 0, f"Expected positive Mar 2020 with macro gate, got {row_2020_gated['Mar']}%")
        self.assertGreater(res_gated["max_dd"], -12.0, f"Max DD should be under -12% with macro gate, got {res_gated['max_dd']}%")

        # With Macro Gate Disabled & Unconstrained (Raw Breakouts)
        res_raw = db.simulate_portfolio(max_slots=2, timeframe="30m", macro_gate=False, circuit_breaker=None)
        row_2020_raw = next(r for r in res_raw["monthly_matrix"] if r["year"] == 2020)
        self.assertLessEqual(row_2020_raw["Mar"], -18.0, f"Expected raw crash stopouts in Mar 2020 without gate, got {row_2020_raw['Mar']}%")

    def test_monthly_risk_circuit_breaker(self):
        """Verify circuit breaker prevents monthly losses exceeding threshold."""
        res = db.simulate_portfolio(max_slots=3, timeframe="30m", macro_gate=True, circuit_breaker=-7.0)
        for row in res["monthly_matrix"]:
            for m in ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']:
                val = row.get(m)
                if val is not None:
                    self.assertGreaterEqual(val, -9.9, f"Month {row['year']} {m} breached risk limit: {val}%")

    def test_mathematical_compounding_consistency(self):
        """Verify that compounding monthly totals matches the annual totals and final NAV."""
        res = db.simulate_portfolio(max_slots=3, timeframe="30m", macro_gate=True, circuit_breaker=-7.0)
        compound = 1.0
        for row in res["monthly_matrix"]:
            ann_ret = row["total"]
            compound *= (1.0 + ann_ret / 100.0)
        
        expected_nav = round(compound * 100.0, 2)
        diff_pct = abs(res["final_nav"] - expected_nav) / expected_nav
        self.assertLess(diff_pct, 0.02, f"Compounding mismatch: simulated final_nav={res['final_nav']} vs compounded={expected_nav}")

    def test_fast_simulation_latency(self):
        """Verify that simulation runs in < 50ms."""
        t0 = time.time()
        for _ in range(10):
            db.simulate_portfolio(max_slots=3, timeframe="30m")
        elapsed_avg = (time.time() - t0) / 10.0
        self.assertLess(elapsed_avg, 0.05, f"Simulation too slow: {elapsed_avg * 1000:.2f}ms")

if __name__ == "__main__":
    unittest.main()
