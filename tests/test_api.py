"""
Unit tests for the FastAPI REST API endpoints.
Uses a temporary DuckDB populated with sample listings so no live scrape is needed.
"""

import importlib
import tempfile
from pathlib import Path

import pytest
import duckdb
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_ROWS = [
    (
        "Depto 1 dorm Providencia",
        363000.0,
        9.5,
        "Providencia",
        "Providencia",
        1,
        1,
        35.0,
        10371.0,
        "Económico",
        "https://portal.com/1",
    ),
    (
        "Loft Santiago Centro",
        280000.0,
        7.3,
        "Santiago",
        "Santiago",
        1,
        1,
        28.0,
        10000.0,
        "Económico",
        "https://portal.com/2",
    ),
    (
        "Depto 3 dorm Las Condes",
        650000.0,
        17.0,
        "Las Condes",
        "Las Condes",
        3,
        2,
        75.0,
        8666.0,
        "Premium",
        "https://portal.com/3",
    ),
    (
        "Depto 2 dorm Ñuñoa",
        420000.0,
        11.0,
        "Ñuñoa",
        "Ñuñoa",
        2,
        1,
        50.0,
        8400.0,
        "Medio",
        "https://portal.com/4",
    ),
    (
        "Casa 4 dorm Vitacura",
        900000.0,
        23.5,
        "Vitacura",
        "Vitacura",
        4,
        3,
        120.0,
        7500.0,
        "Lujo",
        "https://portal.com/5",
    ),
]

COLUMNS = [
    "title",
    "price_clp",
    "price_uf",
    "neighbourhood",
    "comuna",
    "bedrooms",
    "bathrooms",
    "sqm",
    "price_per_sqm",
    "budget_category",
    "url",
]


@pytest.fixture(scope="module")
def tmp_db():
    """Create a temporary DuckDB with the listings table populated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "listings.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute(
            """
            CREATE TABLE listings (
                title VARCHAR,
                price_clp DOUBLE,
                price_uf DOUBLE,
                neighbourhood VARCHAR,
                comuna VARCHAR,
                bedrooms INTEGER,
                bathrooms INTEGER,
                sqm DOUBLE,
                price_per_sqm DOUBLE,
                budget_category VARCHAR,
                url VARCHAR
            )
        """
        )
        for row in SAMPLE_ROWS:
            con.execute("INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", list(row))
        con.close()
        yield db_path


@pytest.fixture(scope="module")
def client(tmp_db, monkeypatch_module):
    """TestClient with DB_PATH patched to the temp database."""
    import src.load as load_mod

    monkeypatch_module.setattr(load_mod, "DB_PATH", tmp_db)

    import src.api as api_mod

    importlib.reload(api_mod)

    return TestClient(api_mod.app)


@pytest.fixture(scope="module")
def monkeypatch_module():
    """Module-scoped monkeypatch (pytest's built-in is function-scoped)."""
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    yield mp
    mp.undo()


# ── Health ────────────────────────────────────────────────────────────────────


def test_health_returns_200(client):
    r = client.get("/api/health")
    assert r.status_code == 200


def test_health_db_exists_true(client):
    r = client.get("/api/health")
    data = r.json()
    assert data["status"] == "ok"
    assert data["db_exists"] is True


# ── Summary ───────────────────────────────────────────────────────────────────


def test_summary_returns_200(client):
    r = client.get("/api/summary")
    assert r.status_code == 200


def test_summary_total_listings(client):
    r = client.get("/api/summary")
    assert r.json()["total_listings"] == 5


def test_summary_has_required_fields(client):
    r = client.get("/api/summary")
    data = r.json()
    required = {
        "total_listings",
        "comunas",
        "avg_price_clp",
        "median_price_clp",
        "avg_sqm",
        "min_price_clp",
        "max_price_clp",
    }
    assert required.issubset(data.keys())


def test_summary_comunas_count(client):
    r = client.get("/api/summary")
    assert r.json()["comunas"] == 5


# ── Listings ──────────────────────────────────────────────────────────────────


def test_listings_returns_200(client):
    r = client.get("/api/listings")
    assert r.status_code == 200


def test_listings_total_count(client):
    r = client.get("/api/listings")
    assert r.json()["total"] == 5


def test_listings_filter_by_comuna(client):
    r = client.get("/api/listings?comuna=Providencia")
    data = r.json()
    assert data["total"] == 1
    assert data["results"][0]["comuna"] == "Providencia"


def test_listings_filter_by_bedrooms(client):
    r = client.get("/api/listings?bedrooms=1")
    data = r.json()
    assert data["total"] == 2
    for row in data["results"]:
        assert row["bedrooms"] == 1


def test_listings_filter_by_min_price(client):
    r = client.get("/api/listings?min_price=500000")
    data = r.json()
    assert data["total"] == 2
    for row in data["results"]:
        assert row["price_clp"] >= 500000


def test_listings_filter_by_max_price(client):
    r = client.get("/api/listings?max_price=400000")
    data = r.json()
    assert data["total"] == 2
    for row in data["results"]:
        assert row["price_clp"] <= 400000


def test_listings_pagination_limit(client):
    r = client.get("/api/listings?limit=2")
    data = r.json()
    assert len(data["results"]) == 2
    assert data["total"] == 5


def test_listings_pagination_offset(client):
    r = client.get("/api/listings?limit=2&offset=4")
    data = r.json()
    assert len(data["results"]) == 1


def test_listings_invalid_limit_zero(client):
    r = client.get("/api/listings?limit=0")
    assert r.status_code == 422


def test_listings_invalid_limit_too_large(client):
    r = client.get("/api/listings?limit=501")
    assert r.status_code == 422


def test_listings_invalid_offset_negative(client):
    r = client.get("/api/listings?offset=-1")
    assert r.status_code == 422


# ── Comunas ───────────────────────────────────────────────────────────────────


def test_comunas_returns_200(client):
    r = client.get("/api/comunas")
    assert r.status_code == 200


def test_comunas_count(client):
    r = client.get("/api/comunas")
    assert len(r.json()) == 5


def test_comunas_fields(client):
    r = client.get("/api/comunas")
    row = r.json()[0]
    assert {"comuna", "total", "avg_price_clp", "avg_sqm"}.issubset(row.keys())


# ── Prices by-bedrooms ────────────────────────────────────────────────────────


def test_prices_by_bedrooms_returns_200(client):
    r = client.get("/api/prices/by-bedrooms")
    assert r.status_code == 200


def test_prices_by_bedrooms_sorted(client):
    r = client.get("/api/prices/by-bedrooms")
    bedrooms = [row["bedrooms"] for row in r.json()]
    assert bedrooms == sorted(bedrooms)


# ── Data quality ──────────────────────────────────────────────────────────────


def test_data_quality_returns_200(client):
    r = client.get("/api/data-quality")
    assert r.status_code == 200


def test_data_quality_has_required_fields(client):
    r = client.get("/api/data-quality")
    data = r.json()
    required = {
        "rows_total",
        "missing_bedrooms",
        "missing_bathrooms",
        "missing_sqm",
        "duplicate_urls",
        "min_price_clp",
        "max_price_clp",
        "avg_price_clp",
        "generated_at",
    }
    assert required.issubset(data.keys())


def test_data_quality_rows_total(client):
    r = client.get("/api/data-quality")
    assert r.json()["rows_total"] == 5


def test_data_quality_no_missing_in_sample(client):
    r = client.get("/api/data-quality")
    data = r.json()
    assert data["missing_bedrooms"] == 0
    assert data["missing_bathrooms"] == 0
    assert data["missing_sqm"] == 0


def test_data_quality_no_duplicate_urls(client):
    r = client.get("/api/data-quality")
    assert r.json()["duplicate_urls"] == 0


def test_data_quality_price_range(client):
    r = client.get("/api/data-quality")
    data = r.json()
    assert data["min_price_clp"] == 280000.0
    assert data["max_price_clp"] == 900000.0


def test_data_quality_generated_at_is_iso(client):
    r = client.get("/api/data-quality")
    from datetime import datetime

    ts = r.json()["generated_at"]
    # Should parse without error
    datetime.fromisoformat(ts)


# ── CSV export ────────────────────────────────────────────────────────────────


def test_export_csv_returns_200(client):
    r = client.get("/api/export/csv")
    assert r.status_code == 200


def test_export_csv_content_type(client):
    r = client.get("/api/export/csv")
    assert "text/csv" in r.headers["content-type"]


def test_export_csv_has_rows(client):
    r = client.get("/api/export/csv")
    lines = r.text.strip().split("\n")
    assert len(lines) == 6  # header + 5 rows


def test_export_csv_filter_by_comuna(client):
    r = client.get("/api/export/csv?comuna=Vitacura")
    lines = r.text.strip().split("\n")
    assert len(lines) == 2  # header + 1 row
    assert "Vitacura" in lines[1]


# ── Excel export ──────────────────────────────────────────────────────────────


def test_export_excel_returns_200(client):
    r = client.get("/api/export/excel")
    assert r.status_code == 200


def test_export_excel_content_type(client):
    r = client.get("/api/export/excel")
    assert "spreadsheetml" in r.headers["content-type"]


def test_export_excel_has_data(client):
    import io
    import openpyxl

    r = client.get("/api/export/excel")
    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    ws = wb.active
    assert ws.max_row == 6  # header + 5 rows
