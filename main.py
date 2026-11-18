"""
main.py - Quant strategy showcase (index-level, published with a delay).
Every number on the pages comes from the exporter's files (see db.py); nothing is typed into the templates.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="Sector Index Momentum - Strategy Showcase", version="2.0.0")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

PROFILE = {
    "github_url": "https://github.com/shubhamsinha1107",
    "linkedin_url": "https://www.linkedin.com/in/shubham-sinha-7a3285300",
    "author_name": "Shubham Sinha",
    "author_title": "Investment Analyst | Portfolio Analytics & Quantitative Research",
}


def _base() -> Dict[str, Any]:
    metrics = db.get_summary_metrics()
    return {
        **PROFILE,
        "meta": db.get_meta(),
        "master": next((m for m in metrics if m.get("type") == "master"), {}),
        "sleeves": [m for m in metrics if m.get("type") == "sleeve"],
    }


NO_DATA = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Strategy Showcase</title></head><body style="font-family:system-ui,sans-serif;max-width:560px;margin:15vh auto;padding:0 16px;color:#1e293b">
<h1 style="font-size:20px">Data not available yet</h1><p>This copy of the showcase has no exported results. The numbers are produced by the
exporter (exporter/run_export.sh) and are not stored in the repository.</p></body></html>"""


def render(name: str, request: Request, ctx: Dict[str, Any]):
    if not ctx.get("meta"):
        return HTMLResponse(NO_DATA, status_code=503)
    return templates.TemplateResponse(request=request, name=name, context={**ctx, "request": request})


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def home(request: Request):
    ctx = _base()
    recent, total = db.get_trades(limit=15)
    ctx.update({
        "index_metrics": db.get_index_metrics(),
        "annual": db.get_annual_returns(),
        "monthly": db.get_monthly_matrix(),
        "sample_trades": recent,
        "total_trades": total,
        "universe": db.get_universe(),
    })
    return render("index.html", request, ctx)


@app.api_route("/explainer", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def explainer(request: Request):
    ctx = _base()
    ctx.update({"annual": db.get_annual_returns(), "index_metrics": db.get_index_metrics()})
    return render("one_pager.html", request, ctx)


@app.api_route("/trades", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def trade_explorer(request: Request, index: Optional[str] = Query(None), sleeve: Optional[str] = Query(None),
                         page: int = Query(1, ge=1), page_size: int = Query(50, ge=10, le=200)):
    trades, total = db.get_trades(limit=page_size, offset=(page - 1) * page_size, index_sym=index, sleeve=sleeve)
    ctx = _base()
    ctx.update({
        "trades": trades, "total": total, "page": page, "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "selected_index": index or "", "selected_sleeve": sleeve or "",
        "indices": [u["name"] for u in db.get_universe()],
    })
    return render("trades.html", request, ctx)


# ── JSON API ────────────────────────────────────────────────────────────────
@app.get("/api/meta")
async def api_meta():
    return JSONResponse(db.get_meta())


@app.get("/api/equity")
async def api_equity():
    return JSONResponse(db.get_equity_series())


@app.get("/api/summary")
async def api_summary():
    return JSONResponse(db.get_summary_metrics())


@app.get("/api/indices")
async def api_indices():
    return JSONResponse(db.get_index_metrics())


@app.get("/api/annual")
async def api_annual():
    return JSONResponse(db.get_annual_returns())


@app.get("/api/monthly")
async def api_monthly():
    return JSONResponse(db.get_monthly_matrix())


@app.get("/api/trades")
async def api_trades(index: Optional[str] = None, sleeve: Optional[str] = None,
                     limit: int = Query(50, ge=1, le=1000), offset: int = Query(0, ge=0)):
    trades, total = db.get_trades(limit=limit, offset=offset, index_sym=index, sleeve=sleeve)
    return JSONResponse({"total": total, "trades": trades, "limit": limit, "offset": offset})


def _list(v: Any) -> Optional[List[str]]:
    if v is None:
        return None
    if isinstance(v, str):
        v = v.split(",")
    out = [str(x).strip() for x in v if str(x).strip()]
    return out or None


def _num(v: Any) -> Optional[float]:
    if v is None or str(v).strip().lower() in ("", "none", "off", "null"):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


@app.get("/api/simulate")
async def api_simulate_get(strategies: Optional[str] = None, universe: Optional[str] = None,
                           cost: Optional[str] = None, monthly_stop: Optional[str] = None):
    u = _list(universe)
    return JSONResponse(db.simulate_portfolio(_list(strategies), [x.upper() for x in u] if u else None,
                                              _num(cost), _num(monthly_stop)))


@app.post("/api/simulate")
async def api_simulate_post(payload: Dict[str, Any]):
    u = _list(payload.get("universe"))
    return JSONResponse(db.simulate_portfolio(_list(payload.get("strategies")), [x.upper() for x in u] if u else None,
                                              _num(payload.get("cost")), _num(payload.get("monthly_stop"))))


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    meta = db.get_meta()
    return {"status": "healthy" if meta else "no-data", "data_through": meta.get("cutoff"),
            "generated_at": meta.get("generated_at")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=False)
