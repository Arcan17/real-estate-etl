"""
Unit tests for the transform module.
"""
import sys
import os
import pytest
import polars as pl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from transform import clean, _parse_price, _parse_bathrooms


def make_df(**overrides) -> pl.DataFrame:
    """Create a minimal valid listings DataFrame for testing."""
    base = {
        "id": [1, 2, 3],
        "name": ["Apt A", "Apt B", "Apt C"],
        "neighbourhood_cleansed": ["Providencia", "Las Condes", "Santiago"],
        "latitude": [-33.43, -33.40, -33.45],
        "longitude": [-70.62, -70.57, -70.65],
        "room_type": ["Entire home/apt", "Private room", "Entire home/apt"],
        "accommodates": ["2", "1", "4"],
        "bedrooms": ["1", "1", "2"],
        "bathrooms_text": ["1 bath", "Shared half-bath", "2 baths"],
        "price": ["$80.00", "$35.00", "$150.00"],
        "minimum_nights": ["2", "1", "3"],
        "maximum_nights": ["30", "365", "60"],
        "number_of_reviews": ["10", "5", "50"],
        "review_scores_rating": ["4.9", "4.3", "4.6"],
        "availability_365": ["100", "200", "50"],
        "instant_bookable": ["t", "f", "t"],
    }
    base.update(overrides)
    return pl.DataFrame(base)


# --- _parse_price ---

def test_parse_price_standard():
    s = pl.Series(["$80.00", "$1,234.50", "$0.00"])
    result = _parse_price(s)
    assert result[0] == pytest.approx(80.0)
    assert result[1] == pytest.approx(1234.5)
    assert result[2] == pytest.approx(0.0)


def test_parse_price_null_on_invalid():
    s = pl.Series(["N/A", "", None])
    result = _parse_price(s)
    assert result.is_null().all()


# --- _parse_bathrooms ---

def _eval_bathrooms(values: list) -> list:
    """Helper: evaluate _parse_bathrooms expression through a DataFrame."""
    s = pl.Series("bathrooms_text", values)
    return pl.select(_parse_bathrooms(s)).to_series().to_list()


def test_parse_bathrooms_whole():
    result = _eval_bathrooms(["1 bath", "2 baths", "3 baths"])
    assert result == [1.0, 2.0, 3.0]


def test_parse_bathrooms_half():
    result = _eval_bathrooms(["Shared half-bath", "Half-bath"])
    assert result[0] == pytest.approx(0.5)
    assert result[1] == pytest.approx(0.5)


def test_parse_bathrooms_decimal():
    result = _eval_bathrooms(["1.5 baths"])
    assert result[0] == pytest.approx(1.5)


# --- clean ---

def test_clean_returns_dataframe():
    df = clean(make_df())
    assert isinstance(df, pl.DataFrame)


def test_clean_removes_zero_price():
    df = make_df(price=["$0.00", "$50.00", "$100.00"])
    result = clean(df)
    assert (result["price_usd"] > 0).all()


def test_clean_removes_null_price():
    df = make_df(price=["N/A", "$50.00", "$100.00"])
    result = clean(df)
    assert len(result) == 2


def test_clean_removes_extreme_price():
    df = make_df(price=["$99999.00", "$50.00", "$100.00"])
    result = clean(df)
    prices = result["price_usd"].to_list()
    assert all(p < 10_000 for p in prices)


def test_clean_adds_price_per_bedroom():
    df = clean(make_df())
    assert "price_per_bedroom" in df.columns
    assert (df["price_per_bedroom"] > 0).all()


def test_clean_adds_occupancy_rate():
    df = clean(make_df())
    assert "occupancy_rate" in df.columns
    assert (df["occupancy_rate"] >= 0).all()
    assert (df["occupancy_rate"] <= 1).all()


def test_clean_adds_rating_category():
    df = clean(make_df())
    assert "rating_category" in df.columns
    valid = {"Excellent", "Very Good", "Good", "Below Average", "No Rating"}
    assert set(df["rating_category"].unique().to_list()).issubset(valid)


def test_clean_rating_excellent_threshold():
    df = make_df(review_scores_rating=["4.9", "4.7", "4.3"])
    result = clean(df)
    cats = result["rating_category"].to_list()
    assert cats[0] == "Excellent"
    assert cats[1] == "Very Good"


def test_clean_instant_bookable_is_bool():
    df = clean(make_df())
    assert df["instant_bookable"].dtype == pl.Boolean


def test_clean_neighbourhood_no_nulls():
    df = make_df(neighbourhood_cleansed=["Providencia", None, "Santiago"])
    result = clean(df)
    assert result["neighbourhood_cleansed"].is_null().sum() == 0


def test_clean_drops_original_price_column():
    df = clean(make_df())
    assert "price" not in df.columns
