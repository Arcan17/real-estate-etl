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
    con.execute("DROP TABLE IF EXISTS listings")
    con.execute("""
        CREATE TABLE listings (
            title           VARCHAR,
            price_clp       DOUBLE,
            neighbourhood   VARCHAR,
            comuna          VARCHAR,
            bedrooms        INTEGER,
            bathrooms       INTEGER,
            sqm             INTEGER,
            location_full   VARCHAR,
            url             VARCHAR,
            price_per_sqm   DOUBLE,
            price_uf        DOUBLE,
            budget_category VARCHAR
        )
    """)


def load(df: pl.DataFrame, con: duckdb.DuckDBPyConnection) -> int:
    con.register("staging", df.to_arrow())
    cols = ", ".join(df.columns)
    con.execute(f"INSERT INTO listings ({cols}) SELECT {cols} FROM staging")
    return con.execute("SELECT COUNT(*) FROM listings").fetchone()[0]


def load_pipeline(df: pl.DataFrame, db_path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    con = get_connection(db_path)
    create_schema(con)
    n = load(df, con)
    print(f"  Loaded {n:,} listings into DuckDB → {db_path.name}")
    return con
