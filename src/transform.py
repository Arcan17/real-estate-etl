"""
Transform: cleans and standardizes scraped Portal Inmobiliario listings using Polars.
"""
import polars as pl
from pathlib import Path


def load_raw(path: Path) -> pl.DataFrame:
    return pl.read_csv(path, infer_schema_length=500, ignore_errors=True)


def clean(df: pl.DataFrame) -> pl.DataFrame:
    # Cast numeric columns
    df = df.with_columns([
        pl.col("price_clp").cast(pl.Float64, strict=False),
        pl.col("bedrooms").cast(pl.Int32, strict=False),
        pl.col("bathrooms").cast(pl.Int32, strict=False),
        pl.col("sqm").cast(pl.Int32, strict=False),
        pl.col("neighbourhood").str.strip_chars().fill_null("Unknown"),
        pl.col("comuna").str.strip_chars().fill_null("Unknown"),
        pl.col("title").str.strip_chars().fill_null(""),
        pl.col("url").str.strip_chars().fill_null(""),
    ])

    # Business rules: drop invalid rows
    df = df.filter(
        pl.col("price_clp").is_not_null() &
        (pl.col("price_clp") > 50_000) &       # min CL$50.000/mes
        (pl.col("price_clp") < 10_000_000)     # max CL$10M/mes
    )

    # Derived columns
    df = df.with_columns([
        # Price per sqm
        pl.when(pl.col("sqm").is_not_null() & (pl.col("sqm") > 0))
          .then(pl.col("price_clp") / pl.col("sqm"))
          .otherwise(None)
          .alias("price_per_sqm"),

        # Price in UF approx (1 UF ≈ CL$38.000)
        (pl.col("price_clp") / 38_000).round(2).alias("price_uf"),

        # Budget category
        pl.when(pl.col("price_clp") < 300_000).then(pl.lit("Económico"))
          .when(pl.col("price_clp") < 600_000).then(pl.lit("Medio"))
          .when(pl.col("price_clp") < 1_000_000).then(pl.lit("Premium"))
          .otherwise(pl.lit("Lujo"))
          .alias("budget_category"),
    ])

    return df


def save_parquet(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    print(f"  Saved: {path.name} ({len(df):,} rows, {path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    from pathlib import Path
    raw = Path(__file__).parent.parent / "data" / "raw" / "listings_raw.csv"
    df = clean(load_raw(raw))
    print(df.glimpse())
