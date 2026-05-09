"""
FastAPI REST API for the Real Estate ETL Pipeline.
Run: uvicorn src.api:app --reload
"""

import io
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import polars as pl
import duckdb

from load import DB_PATH, get_connection

app = FastAPI(
    title="Real Estate ETL API — Santiago, Chile",
    description="REST API over scraped Portal Inmobiliario listings stored in DuckDB.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_df() -> pl.DataFrame:
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="No data. Run `python src/main.py` first.")
    con = get_connection(DB_PATH)
    return pl.from_arrow(con.execute("SELECT * FROM listings").arrow())


# ── Endpoints ─────────────────────────────────────────────────────────────────


@app.get("/api/health")
def health():
    return {"status": "ok", "db_exists": DB_PATH.exists()}


@app.get("/api/listings")
def get_listings(
    comuna: str = Query(None, description="Filter by comuna"),
    min_price: float = Query(None, description="Minimum price CLP"),
    max_price: float = Query(None, description="Maximum price CLP"),
    bedrooms: int = Query(None, description="Number of bedrooms"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    """Return paginated listings with optional filters."""
    df = _get_df()
    if comuna:
        df = df.filter(pl.col("comuna") == comuna)
    if min_price is not None:
        df = df.filter(pl.col("price_clp") >= min_price)
    if max_price is not None:
        df = df.filter(pl.col("price_clp") <= max_price)
    if bedrooms is not None:
        df = df.filter(pl.col("bedrooms") == bedrooms)

    total = len(df)
    page = df.slice(offset, limit)
    return {"total": total, "offset": offset, "limit": limit, "results": page.to_dicts()}


@app.get("/api/summary")
def get_summary():
    """Market summary statistics."""
    df = _get_df()
    return {
        "total_listings": len(df),
        "comunas": df["comuna"].drop_nulls().n_unique(),
        "avg_price_clp": round(df["price_clp"].mean(), 0),
        "median_price_clp": round(df["price_clp"].median(), 0),
        "avg_sqm": round(df["sqm"].drop_nulls().mean(), 1),
        "min_price_clp": df["price_clp"].min(),
        "max_price_clp": df["price_clp"].max(),
    }


@app.get("/api/comunas")
def get_comunas():
    """List all comunas with listing count and average price."""
    df = _get_df()
    result = (
        df.filter(pl.col("comuna").is_not_null())
        .group_by("comuna")
        .agg(
            [
                pl.count("price_clp").alias("total"),
                pl.mean("price_clp").alias("avg_price_clp"),
                pl.mean("sqm").alias("avg_sqm"),
            ]
        )
        .sort("avg_price_clp", descending=True)
    )
    return result.to_dicts()


@app.get("/api/prices/by-comuna")
def prices_by_comuna(top: int = Query(15, le=50)):
    """Average price per commune, sorted descending."""
    df = _get_df()
    result = (
        df.filter(pl.col("comuna").is_not_null())
        .group_by("comuna")
        .agg(pl.mean("price_clp").alias("avg_price_clp"))
        .sort("avg_price_clp", descending=True)
        .head(top)
    )
    return result.to_dicts()


@app.get("/api/prices/by-bedrooms")
def prices_by_bedrooms():
    """Average price and sqm per bedroom count."""
    df = _get_df()
    result = (
        df.filter(pl.col("bedrooms").is_not_null() & pl.col("bedrooms").is_between(1, 5))
        .group_by("bedrooms")
        .agg(
            [
                pl.mean("price_clp").alias("avg_price_clp"),
                pl.mean("sqm").alias("avg_sqm"),
                pl.count("price_clp").alias("total"),
            ]
        )
        .sort("bedrooms")
    )
    return result.to_dicts()


@app.get("/api/export/csv")
def export_csv(comuna: str = Query(None), bedrooms: int = Query(None)):
    """Download all listings as CSV."""
    df = _get_df()
    if comuna:
        df = df.filter(pl.col("comuna") == comuna)
    if bedrooms is not None:
        df = df.filter(pl.col("bedrooms") == bedrooms)

    csv_bytes = df.write_csv().encode("utf-8")
    filename = f"listings{'_' + comuna if comuna else ''}.csv"
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/export/excel")
def export_excel(comuna: str = Query(None), bedrooms: int = Query(None)):
    """Download all listings as Excel (.xlsx)."""
    df = _get_df()
    if comuna:
        df = df.filter(pl.col("comuna") == comuna)
    if bedrooms is not None:
        df = df.filter(pl.col("bedrooms") == bedrooms)

    buf = io.BytesIO()
    df.to_pandas().to_excel(buf, index=False, sheet_name="Listings")
    buf.seek(0)

    filename = f"listings{'_' + comuna if comuna else ''}.xlsx"
    media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(
        buf,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
