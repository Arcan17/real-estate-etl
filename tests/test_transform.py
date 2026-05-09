"""
Unit tests for the transform module — Portal Inmobiliario ETL.
"""
import sys
import os
import pytest
import polars as pl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from transform import clean


def make_df(**overrides) -> pl.DataFrame:
    """Create a minimal valid listings DataFrame for testing."""
    base = {
        "title":        ["Depto 1 dorm Providencia", "Loft Santiago Centro", "Depto 3 dorm Las Condes"],
        "price_clp":    ["363000", "280000", "650000"],
        "neighbourhood":["Providencia", "Santiago", "Las Condes"],
        "comuna":       ["Providencia", "Santiago", "Las Condes"],
        "bedrooms":     ["1", "1", "3"],
        "bathrooms":    ["1", "1", "2"],
        "sqm":          ["35", "28", "75"],
        "location_full":["Providencia, Santiago", "Santiago Centro", "Las Condes, Santiago"],
        "url":          ["https://portal.com/1", "https://portal.com/2", "https://portal.com/3"],
    }
    base.update(overrides)
    return pl.DataFrame(base)


# ── clean() — basic contract ──────────────────────────────────────────────────

def test_clean_returns_dataframe():
    result = clean(make_df())
    assert isinstance(result, pl.DataFrame)


def test_clean_casts_price_to_float():
    result = clean(make_df())
    assert result["price_clp"].dtype == pl.Float64


def test_clean_casts_bedrooms_to_int():
    result = clean(make_df())
    assert result["bedrooms"].dtype == pl.Int32


def test_clean_casts_bathrooms_to_int():
    result = clean(make_df())
    assert result["bathrooms"].dtype == pl.Int32


def test_clean_casts_sqm_to_int():
    result = clean(make_df())
    assert result["sqm"].dtype == pl.Int32


# ── Business rules — price filtering ─────────────────────────────────────────

def test_clean_drops_price_below_minimum():
    df = make_df(price_clp=["30000", "363000", "500000"])  # 30k < 50k threshold
    result = clean(df)
    assert len(result) == 2
    assert (result["price_clp"] >= 50_000).all()


def test_clean_drops_price_above_maximum():
    df = make_df(price_clp=["363000", "12000000", "500000"])  # 12M > 10M threshold
    result = clean(df)
    assert len(result) == 2
    assert (result["price_clp"] < 10_000_000).all()


def test_clean_drops_null_price():
    df = make_df(price_clp=["N/A", "363000", "500000"])
    result = clean(df)
    assert len(result) == 2


def test_clean_keeps_valid_prices():
    result = clean(make_df())
    assert len(result) == 3


# ── Derived columns ───────────────────────────────────────────────────────────

def test_clean_adds_price_uf():
    result = clean(make_df())
    assert "price_uf" in result.columns
    # 363000 / 38000 ≈ 9.55
    assert result["price_uf"][0] == pytest.approx(363000 / 38000, rel=1e-3)


def test_clean_adds_price_per_sqm():
    result = clean(make_df())
    assert "price_per_sqm" in result.columns
    # 363000 / 35 ≈ 10371
    assert result["price_per_sqm"][0] == pytest.approx(363000 / 35, rel=1e-3)


def test_clean_price_per_sqm_null_when_sqm_missing():
    df = make_df(sqm=[None, "28", "75"])
    result = clean(df)
    assert result["price_per_sqm"][0] is None


def test_clean_adds_budget_category():
    result = clean(make_df())
    assert "budget_category" in result.columns
    valid = {"Económico", "Medio", "Premium", "Lujo"}
    assert set(result["budget_category"].unique().to_list()).issubset(valid)


# ── Budget category thresholds ────────────────────────────────────────────────

def test_budget_economico_below_300k():
    df = make_df(price_clp=["250000", "363000", "650000"])
    result = clean(df)
    assert result["budget_category"][0] == "Económico"


def test_budget_medio_300k_to_600k():
    df = make_df(price_clp=["363000", "363000", "363000"])
    result = clean(df)
    assert (result["budget_category"] == "Medio").all()


def test_budget_premium_600k_to_1m():
    df = make_df(price_clp=["700000", "363000", "363000"])
    result = clean(df)
    assert result["budget_category"][0] == "Premium"


def test_budget_lujo_above_1m():
    df = make_df(price_clp=["1500000", "363000", "363000"])
    result = clean(df)
    assert result["budget_category"][0] == "Lujo"


# ── Null handling ─────────────────────────────────────────────────────────────

def test_clean_fills_null_comuna():
    df = make_df(comuna=["Providencia", None, "Las Condes"])
    result = clean(df)
    assert result["comuna"].is_null().sum() == 0
    assert result["comuna"][1] == "Unknown"


def test_clean_fills_null_neighbourhood():
    df = make_df(neighbourhood=["Providencia", None, "Las Condes"])
    result = clean(df)
    assert result["neighbourhood"].is_null().sum() == 0
    assert result["neighbourhood"][1] == "Unknown"
