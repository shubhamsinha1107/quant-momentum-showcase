"""
seed_db.py - Initializes database schema and seeds pure index backtest data into Neon Postgres or SQLite.
"""
import os
import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        import psycopg2
        url = DATABASE_URL.replace("postgres://", "postgresql://")
        return psycopg2.connect(url)
    else:
        db_path = DATA_DIR / "showcase.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

def clean_num(val, is_float=True):
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        return float(val) if is_float else int(val)
    s = str(val).replace("%", "").replace(",", "").strip()
    try:
        return float(s) if is_float else int(round(float(s)))
    except (ValueError, TypeError):
        return None

def run_seed():
    conn = get_connection()
    is_postgres = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))
    cur = conn.cursor()

    force_seed = os.getenv("FORCE_SEED", "false").lower() in ("true", "1")
    if not force_seed:
        try:
            if is_postgres:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'summary_metrics'
                    );
                """)
                exists = cur.fetchone()[0]
                if exists:
                    cur.execute("SELECT COUNT(*) FROM summary_metrics;")
                    if cur.fetchone()[0] >= 4:
                        print("[SEED] Neon PostgreSQL tables already populated. Ready for instant traffic.")
                        conn.close()
                        return
            else:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='summary_metrics';")
                if cur.fetchone():
                    cur.execute("SELECT COUNT(*) FROM summary_metrics;")
                    if cur.fetchone()[0] >= 4:
                        print("[SEED] SQLite tables already populated. Ready for instant traffic.")
                        conn.close()
                        return
        except Exception as e:
            if is_postgres:
                conn.rollback()

    print(f"[SEED] Initializing database (Postgres: {is_postgres})...")

    # Drop old tables to guarantee clean re-seeding
    if is_postgres:
        cur.execute("""
            DROP TABLE IF EXISTS k_sensitivity CASCADE;
            DROP TABLE IF EXISTS summary_metrics CASCADE;
            DROP TABLE IF EXISTS index_metrics CASCADE;
            DROP TABLE IF EXISTS annual_returns CASCADE;
            DROP TABLE IF EXISTS monthly_matrix CASCADE;
            DROP TABLE IF EXISTS trades CASCADE;

            CREATE TABLE summary_metrics (
                id SERIAL PRIMARY KEY,
                name TEXT,
                type TEXT,
                horizon TEXT,
                allocation TEXT,
                trades INT,
                win_rate REAL,
                avg_trade_pct REAL,
                cagr REAL,
                max_dd REAL,
                sharpe REAL,
                sortino REAL,
                calmar REAL,
                profit_factor REAL,
                asset_classes TEXT
            );

            CREATE TABLE index_metrics (
                id SERIAL PRIMARY KEY,
                index_name TEXT,
                trades INT,
                win_rate REAL,
                avg_trade_pct REAL,
                cum_return_pct REAL,
                max_win_pct REAL,
                max_loss_pct REAL,
                profit_factor REAL
            );

            CREATE TABLE annual_returns (
                id SERIAL PRIMARY KEY,
                year TEXT,
                regime TEXT,
                direct_baseline REAL,
                win_rate REAL
            );

            CREATE TABLE monthly_matrix (
                id SERIAL PRIMARY KEY,
                year INT,
                jan REAL, feb REAL, mar REAL, apr REAL, may REAL, jun REAL,
                jul REAL, aug REAL, sep REAL, oct REAL, nov REAL, "dec" REAL,
                total REAL
            );

            CREATE TABLE trades (
                id SERIAL PRIMARY KEY,
                trade_no INT,
                stock TEXT,
                sector_index TEXT,
                entry_time TEXT,
                exit_time TEXT,
                entry_price REAL,
                exit_price REAL,
                return_pct REAL,
                holding_days REAL,
                sleeve TEXT
            );
        """)
    else:
        cur.executescript("""
            DROP TABLE IF EXISTS k_sensitivity;
            DROP TABLE IF EXISTS summary_metrics;
            DROP TABLE IF EXISTS index_metrics;
            DROP TABLE IF EXISTS annual_returns;
            DROP TABLE IF EXISTS monthly_matrix;
            DROP TABLE IF EXISTS trades;

            CREATE TABLE summary_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                horizon TEXT,
                allocation TEXT,
                trades INT,
                win_rate REAL,
                avg_trade_pct REAL,
                cagr REAL,
                max_dd REAL,
                sharpe REAL,
                sortino REAL,
                calmar REAL,
                profit_factor REAL,
                asset_classes TEXT
            );

            CREATE TABLE index_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                index_name TEXT,
                trades INT,
                win_rate REAL,
                avg_trade_pct REAL,
                cum_return_pct REAL,
                max_win_pct REAL,
                max_loss_pct REAL,
                profit_factor REAL
            );

            CREATE TABLE annual_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year TEXT,
                regime TEXT,
                direct_baseline REAL,
                win_rate REAL
            );

            CREATE TABLE monthly_matrix (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INT,
                jan REAL, feb REAL, mar REAL, apr REAL, may REAL, jun REAL,
                jul REAL, aug REAL, sep REAL, oct REAL, nov REAL, "dec" REAL,
                total REAL
            );

            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_no INT,
                stock TEXT,
                sector_index TEXT,
                entry_time TEXT,
                exit_time TEXT,
                entry_price REAL,
                exit_price REAL,
                return_pct REAL,
                holding_days REAL,
                sleeve TEXT
            );
        """)
    conn.commit()

    # Seed Summary Metrics
    p = DATA_DIR / "summary_metrics.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        for m in metrics:
            placeholder = "%s" if is_postgres else "?"
            placeholders = ", ".join([placeholder] * 14)
            cur.execute(f"""
                INSERT INTO summary_metrics (
                    name, type, horizon, allocation, trades, win_rate, avg_trade_pct,
                    cagr, max_dd, sharpe, sortino, calmar, profit_factor, asset_classes
                ) VALUES ({placeholders})
            """, (
                m.get("name"), m.get("type"), m.get("horizon"), m.get("allocation"),
                clean_num(m.get("trades"), False), clean_num(m.get("win_rate")), clean_num(m.get("avg_trade_pct")),
                clean_num(m.get("cagr")), clean_num(m.get("max_dd")), clean_num(m.get("sharpe")),
                clean_num(m.get("sortino")), clean_num(m.get("calmar")), clean_num(m.get("profit_factor")),
                m.get("asset_classes")
            ))
        print(f"[SEED] Loaded {len(metrics)} summary metric rows.")

    # Seed Index Metrics
    p = DATA_DIR / "index_metrics.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            idx_metrics = json.load(f)
        for im in idx_metrics:
            placeholder = "%s" if is_postgres else "?"
            placeholders = ", ".join([placeholder] * 8)
            cur.execute(f"""
                INSERT INTO index_metrics (
                    index_name, trades, win_rate, avg_trade_pct, cum_return_pct, max_win_pct, max_loss_pct, profit_factor
                ) VALUES ({placeholders})
            """, (
                im.get("index"), clean_num(im.get("trades"), False), clean_num(im.get("win_rate")),
                clean_num(im.get("avg_trade_pct")), clean_num(im.get("cum_return_pct")),
                clean_num(im.get("max_win_pct")), clean_num(im.get("max_loss_pct")), clean_num(im.get("profit_factor"))
            ))
        print(f"[SEED] Loaded {len(idx_metrics)} index metric rows.")

    # Seed Annual Returns
    p = DATA_DIR / "annual_returns.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            annual = json.load(f)
        for a in annual:
            ph = "%s" if is_postgres else "?"
            phs = ", ".join([ph] * 4)
            cur.execute(f"""
                INSERT INTO annual_returns (year, regime, direct_baseline, win_rate)
                VALUES ({phs})
            """, (
                str(a.get("year")), a.get("regime"), clean_num(a.get("direct_baseline")), clean_num(a.get("win_rate"))
            ))
        print(f"[SEED] Loaded {len(annual)} annual return rows.")

    # Seed Monthly Matrix
    p = DATA_DIR / "monthly_matrix.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            months = json.load(f)
        for m in months:
            ph = "%s" if is_postgres else "?"
            phs = ", ".join([ph] * 14)
            cur.execute(f"""
                INSERT INTO monthly_matrix (year, jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, "dec", total)
                VALUES ({phs})
            """, (
                clean_num(m.get("year"), False),
                clean_num(m.get("Jan") or m.get("jan")), clean_num(m.get("Feb") or m.get("feb")), clean_num(m.get("Mar") or m.get("mar")),
                clean_num(m.get("Apr") or m.get("apr")), clean_num(m.get("May") or m.get("may")), clean_num(m.get("Jun") or m.get("jun")),
                clean_num(m.get("Jul") or m.get("jul")), clean_num(m.get("Aug") or m.get("aug")), clean_num(m.get("Sep") or m.get("sep")),
                clean_num(m.get("Oct") or m.get("oct")), clean_num(m.get("Nov") or m.get("nov")), clean_num(m.get("Dec") or m.get("dec")),
                clean_num(m.get("Total") if m.get("Total") is not None else m.get("total"))
            ))
        print(f"[SEED] Loaded {len(months)} monthly matrix rows.")

    # Seed Trades
    p = DATA_DIR / "trades.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            trades = json.load(f)
        rows = []
        for t in trades:
            rows.append((
                clean_num(t.get("Trade No"), False), t.get("Stock"), t.get("Index"),
                str(t.get("Entry Time")), str(t.get("Exit Time")),
                clean_num(t.get("Entry Price")), clean_num(t.get("Exit Price")),
                clean_num(t.get("Return_Pct")), clean_num(t.get("Holding Period (days)")),
                t.get("Sleeve")
            ))
        if is_postgres:
            from psycopg2.extras import execute_values
            execute_values(cur, """
                INSERT INTO trades (trade_no, stock, sector_index, entry_time, exit_time, entry_price, exit_price, return_pct, holding_days, sleeve)
                VALUES %s
            """, rows)
        else:
            ph = "?"
            phs = ", ".join([ph] * 10)
            cur.executemany(f"""
                INSERT INTO trades (trade_no, stock, sector_index, entry_time, exit_time, entry_price, exit_price, return_pct, holding_days, sleeve)
                VALUES ({phs})
            """, rows)
        print(f"[SEED] Loaded {len(rows)} direct index trade log rows.")

    conn.commit()
    conn.close()
    print("[SEED] Database initialized and verified successfully.")

if __name__ == "__main__":
    run_seed()
