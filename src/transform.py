"""
Transform: cleans and standardizes raw Airbnb listings using Polars.
Applies business rules, type casting, null handling, and derived columns.
"""
import polars as pl
from pathlib import Path

# Columns we care about — drop everything else
KEEP_COLS = [
    "id", "name", "neighbourhood_cleansed", "latitude", "longitude",
    "room_type", "accommodates", "bedrooms", "bathrooms_text",
    "price", "minimum_nights", "maximum_nights",
    "number_of_reviews", "review_scores_rating",
    "availability_365", "instant_bookable",
]


def _parse_price(series: pl.Series) -> pl.Series:
    """'$1,234.00' → 1234.0"""
    return (
        series
        .str.replace_all(r"[\$,]", "")
        .cast(pl.Float64, strict=False)
    )


def _parse_bathrooms(series: pl.Series) -> pl.Series:
    """'1.5 baths' / 'Shared half-bath' → 1.5 / 0.5"""
    cleaned = series.str.to_lowercase()
    is_half = cleaned.str.contains("half")
    num = cleaned.str.extract(r"(\d+\.?\d*)").cast(pl.Float64, strict=False)
    return pl.when(is_half & num.is_null()).then(0.5).otherwise(num)


def load_raw(path: Path) -> pl.DataFrame:
    """Read the compressed CSV with only the columns we need."""
    available = pl.read_csv(path, n_rows=0, infer_schema_length=0).columns
    cols = [c for c in KEEP_COLS if c in available]
    return pl.read_csv(path, columns=cols, infer_schema_length=500, ignore_errors=True)


def clean(df: pl.DataFrame) -> pl.DataFrame:
    """Apply all transformation and business-rule steps."""

    df = df.with_columns([
        # Price: parse string → float
        _parse_price(pl.col("price")).alias("price_usd"),

        # Bathrooms: parse text → float
        _parse_bathrooms(pl.col("bathrooms_text")).alias("bathrooms"),

        # Numeric casts
        pl.col("bedrooms").cast(pl.Float64, strict=False),
        pl.col("accommodates").cast(pl.Int32, strict=False),
        pl.col("minimum_nights").cast(pl.Int32, strict=False),
        pl.col("number_of_reviews").cast(pl.Int32, strict=False),
        pl.col("review_scores_rating").cast(pl.Float64, strict=False),
        pl.col("availability_365").cast(pl.Int32, strict=False),

        # Boolean
        (pl.col("instant_bookable").str.to_lowercase() == "t").alias("instant_bookable"),

        # Neighbourhood: fill nulls, strip whitespace
        pl.col("neighbourhood_cleansed").str.strip_chars().fill_null("Unknown"),
    ])

    # Business rules: drop rows that violate data quality
    df = df.filter(
        pl.col("price_usd").is_not_null() & (pl.col("price_usd") > 0) & (pl.col("price_usd") < 10_000)
    ).filter(
        pl.col("accommodates").is_not_null() & (pl.col("accommodates") > 0)
    ).filter(
        pl.col("latitude").is_not_null() & pl.col("longitude").is_not_null()
    )

    # Derived columns
    df = df.with_columns([
        # Price per bedroom (handle 0 bedrooms as studio = 1)
        (pl.col("price_usd") / pl.col("bedrooms").fill_null(1).clip(lower_bound=1))
        .alias("price_per_bedroom"),

        # Occupancy proxy: higher availability = less occupied
        (1 - pl.col("availability_365") / 365).alias("occupancy_rate"),

        # Rating category
        pl.when(pl.col("review_scores_rating") >= 4.8).then(pl.lit("Excellent"))
          .when(pl.col("review_scores_rating") >= 4.5).then(pl.lit("Very Good"))
          .when(pl.col("review_scores_rating") >= 4.0).then(pl.lit("Good"))
          .when(pl.col("review_scores_rating").is_not_null()).then(pl.lit("Below Average"))
          .otherwise(pl.lit("No Rating"))
          .alias("rating_category"),
    ])

    return df.drop(["bathrooms_text", "price"])


def save_parquet(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    print(f"  Saved: {path.name} ({len(df):,} rows, {path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    from pathlib import Path
    raw = Path(__file__).parent.parent / "data" / "raw" / "listings_raw.csv.gz"
    df = clean(load_raw(raw))
    print(df.glimpse())
