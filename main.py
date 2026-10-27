"""
main.py - Institutional Quantitative Strategy Showcase
Interactive Backtesting & Research Portal (Main Sector Indices & ETFs)
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db
import seed_db

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(
    title="Quantitative Multi-Asset Sector Momentum Strategy Showcase",
    description="Empirical backtesting and risk analytics portal for major NSE sector indices & multi-asset ETFs.",
    version="1.0.0"
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def render_template(template_name: str, request: Request, context: Optional[Dict[str, Any]] = None):
    """Template renderer for Starlette/FastAPI."""
    ctx = context.copy() if context else {}
    ctx["request"] = request
    return templates.TemplateResponse(request=request, name=template_name, context=ctx)

@app.on_event("startup")
def startup_event():
    """Ensure database schema is created and seeded on boot."""
    try:
        seed_db.run_seed()
    except Exception as e:
        print(f"[STARTUP] Notice during seed: {e}")

# ---------------------------------------------------------
# Web Page Endpoints
# ---------------------------------------------------------

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def home_dashboard(request: Request):
    """Main institutional interactive dashboard."""
    metrics = db.get_summary_metrics()
    index_metrics = db.get_index_metrics()
    annual = db.get_annual_returns()
    monthly = db.get_monthly_matrix()
    sample_trades, total_trades = db.get_trades(limit=15)
    
    master = next((m for m in metrics if m.get("type") == "master"), {})
    sleeves = [m for m in metrics if m.get("type") == "sleeve"]

    return render_template(
        "index.html",
        request,
        {
            "master": master,
            "sleeves": sleeves,
            "index_metrics": index_metrics,
            "annual": annual,
            "monthly": monthly,
            "sample_trades": sample_trades,
            "total_trades": total_trades,
            "github_url": "https://github.com/shubhamsinha1107",
            "linkedin_url": "https://www.linkedin.com/in/shubham-sinha-7a3285300",
            "author_name": "Shubham Sinha",
            "author_title": "Investment Analyst | Portfolio Analytics & Quantitative Research"
        }
    )

@app.api_route("/explainer", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def strategy_explainer(request: Request):
    """Institutional Strategy One-Pager memo (print-ready A4)."""
    return render_template("one_pager.html", request)

@app.api_route("/trades", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def trade_explorer(
    request: Request,
    index: Optional[str] = Query(None),
    sleeve: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200)
):
    """Full-featured paginated trade log explorer."""
    offset = (page - 1) * page_size
    trades, total = db.get_trades(limit=page_size, offset=offset, index_sym=index, sleeve=sleeve)
    total_pages = max(1, (total + page_size - 1) // page_size)
    index_list = db.get_index_metrics()
    
    return render_template(
        "trades.html",
        request,
        {
            "trades": trades,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "selected_index": index or "",
            "selected_sleeve": sleeve or "",
            "indices": [im.get("index_name") or im.get("index") for im in index_list]
        }
    )

# ---------------------------------------------------------
# JSON API Endpoints (For Chart.js & External Evaluation)
# ---------------------------------------------------------

@app.get("/api/equity")
async def api_equity_series():
    """Returns weekly NAV time series for Master Portfolio, Benchmark, and Drawdowns."""
    return JSONResponse(content=db.get_equity_series())

@app.get("/api/summary")
async def api_summary_metrics():
    """Returns high-level summary metrics across sleeves."""
    return JSONResponse(content=db.get_summary_metrics())

@app.get("/api/indices")
async def api_indices_metrics():
    """Returns index-by-index breakdown metrics."""
    return JSONResponse(content=db.get_index_metrics())

@app.get("/api/annual")
async def api_annual_returns():
    """Returns annual returns by market regime."""
    return JSONResponse(content=db.get_annual_returns())

@app.get("/api/monthly")
async def api_monthly_matrix():
    """Returns monthly return matrix (Jan-Dec + Total) from 2020 to 2026."""
    return JSONResponse(content=db.get_monthly_matrix())

@app.get("/api/trades")
async def api_trades(
    index: Optional[str] = None,
    sleeve: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Paginated trade records."""
    trades, total = db.get_trades(limit=limit, offset=offset, index_sym=index, sleeve=sleeve)
    return JSONResponse(content={"total": total, "trades": trades, "limit": limit, "offset": offset})

@app.get("/api/candidates")
async def api_candidates(timeframe: str = "30m"):
    """Returns complete unfiltered ranked candidate trade events for a timeframe."""
    cands = db.get_ranked_candidates(timeframe)
    return JSONResponse(content={"timeframe": timeframe, "total": len(cands), "candidates": cands})

@app.get("/api/simulate")
async def api_simulate_get(
    slots: int = Query(3, ge=1, le=15),
    timeframe: str = Query("30m"),
    universe: Optional[str] = Query(None),
    macro_gate: bool = Query(True),
    circuit_breaker: Optional[str] = Query("-7.0")
):
    """Fast simulation endpoint via GET parameters."""
    u_list = [u.strip().upper() for u in universe.split(",") if u.strip()] if universe else None
    cb_val = None
    if circuit_breaker and circuit_breaker.strip() and circuit_breaker.lower() not in ("none", "null", "off", "0"):
        try:
            cb_val = float(circuit_breaker)
        except Exception:
            cb_val = -7.0
    res = db.simulate_portfolio(
        max_slots=slots,
        timeframe=timeframe,
        universe=u_list,
        macro_gate=macro_gate,
        circuit_breaker=cb_val
    )
    return JSONResponse(content=res)

@app.post("/api/simulate")
async def api_simulate_post(payload: Dict[str, Any]):
    """Fast simulation endpoint via POST JSON payload."""
    slots = int(payload.get("slots", 3))
    timeframe = str(payload.get("timeframe", "30m"))
    universe = payload.get("universe", None)
    if isinstance(universe, str):
        universe = [u.strip().upper() for u in universe.split(",") if u.strip()]
    macro_gate = bool(payload.get("macro_gate", True))
    cb = payload.get("circuit_breaker", "-7.0")
    cb_val = None
    if cb and str(cb).strip() and str(cb).lower() not in ("none", "null", "off", "0"):
        try:
            cb_val = float(cb)
        except Exception:
            cb_val = -7.0
    res = db.simulate_portfolio(
        max_slots=slots,
        timeframe=timeframe,
        universe=universe,
        macro_gate=macro_gate,
        circuit_breaker=cb_val
    )
    return JSONResponse(content=res)

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Healthcheck endpoint for Render / Uptime monitors."""
    return {"status": "healthy", "service": "quant-momentum-showcase", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
