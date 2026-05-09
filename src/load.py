"""
Load: inserts the cleaned Polars DataFrame into a DuckDB analytical database.
"""
import duckdb
import polars as pl
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "listings.duckdb"


def get_connection(db_path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def create_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id                  BIGINT PRIMARY KEY,
            name                VARCHAR,
            neighbourhood       VARCHAR,
            latitude            DOUBLE,
            longitude           DOUBLE,
            room_type           VARCHAR,
            accommodates        INTEGER,
            bedrooms            DOUBLE,
            bathrooms           DOUBLE,
            price_usd           DOUBLE,
            minimum_nights      INTEGER,
            maximum_nights      INTEGER,
            number_of_reviews   INTEGER,
            review_scores_rating DOUBLE,
            availability_365    INTEGER,
            instant_bookable    BOOLEAN,
            price_per_bedroom   DOUBLE,
            occupancy_rate      DOUBLE,
            rating_category     VARCHAR
        )
    """)


def load(df: pl.DataFrame, con: duckdb.DuckDBPyConnection) -> int:
    """Insert-or-replace all rows from the Polars DataFrame."""
    # Rename neighbourhood col to match schema
    if "neighbourhood_cleansed" in df.columns:
        df = df.rename({"neighbourhood_cleansed": "neighbourhood"})

    # Register Polars df as a DuckDB view, then upsert
    # Reorder columns to match the table schema exactly
    schema_cols = [
        "id", "name", "neighbourhood", "latitude", "longitude",
        "room_type", "accommodates", "bedrooms", "bathrooms", "price_usd",
        "minimum_nights", "maximum_nights", "number_of_reviews",
        "review_scores_rating", "availability_365", "instant_bookable",
        "price_per_bedroom", "occupancy_rate", "rating_category",
    ]
    df = df.select([c for c in schema_cols if c in df.columns])

    con.register("staging", df.to_arrow())
    con.execute("DELETE FROM listings")
    cols = ", ".join(df.columns)
    con.execute(f"INSERT INTO listings ({cols}) SELECT {cols} FROM staging")
    count = con.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    return count


def load_pipeline(df: pl.DataFrame, db_path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    con = get_connection(db_path)
    create_schema(con)
    n = load(df, con)
    print(f"  Loaded {n:,} listings into DuckDB → {db_path.name}")
    return con


if __name__ == "__main__":
    print("Run main.py to execute the full pipeline.")
