"""
Analytics: SQL queries on DuckDB to extract insights from the listings data.
"""
import duckdb
import polars as pl
from pathlib import Path


def avg_price_by_neighbourhood(con: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    """Average nightly price per neighbourhood, sorted descending."""
    arrow = con.execute("""
        SELECT
            neighbourhood,
            COUNT(*)                        AS total_listings,
            ROUND(AVG(price_usd), 2)        AS avg_price_usd,
            ROUND(MEDIAN(price_usd), 2)     AS median_price_usd,
            ROUND(AVG(review_scores_rating), 2) AS avg_rating
        FROM listings
        GROUP BY neighbourhood
        HAVING COUNT(*) >= 5
        ORDER BY avg_price_usd DESC
        LIMIT 15
    """).arrow()
    return pl.from_arrow(arrow)


def price_by_room_type(con: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    """Price and occupancy statistics per room type."""
    arrow = con.execute("""
        SELECT
            room_type,
            COUNT(*)                            AS total_listings,
            ROUND(AVG(price_usd), 2)            AS avg_price_usd,
            ROUND(AVG(occupancy_rate) * 100, 1) AS avg_occupancy_pct,
            ROUND(AVG(review_scores_rating), 2) AS avg_rating
        FROM listings
        GROUP BY room_type
        ORDER BY avg_price_usd DESC
    """).arrow()
    return pl.from_arrow(arrow)


def top_value_listings(con: duckdb.DuckDBPyConnection, limit: int = 10) -> pl.DataFrame:
    """Best value listings: high rating, high occupancy, reasonable price."""
    arrow = con.execute(f"""
        SELECT
            id,
            name,
            neighbourhood,
            room_type,
            accommodates,
            bedrooms,
            ROUND(price_usd, 0)                 AS price_usd,
            ROUND(review_scores_rating, 2)       AS rating,
            ROUND(occupancy_rate * 100, 1)       AS occupancy_pct,
            rating_category
        FROM listings
        WHERE review_scores_rating >= 4.5
          AND number_of_reviews >= 10
          AND price_usd BETWEEN 30 AND 300
        ORDER BY review_scores_rating DESC, occupancy_rate DESC
        LIMIT {limit}
    """).arrow()
    return pl.from_arrow(arrow)


def market_summary(con: duckdb.DuckDBPyConnection) -> dict:
    """Overall market statistics."""
    row = con.execute("""
        SELECT
            COUNT(*)                            AS total_listings,
            COUNT(DISTINCT neighbourhood)       AS total_neighbourhoods,
            ROUND(AVG(price_usd), 2)            AS avg_price_usd,
            ROUND(MEDIAN(price_usd), 2)         AS median_price_usd,
            ROUND(AVG(occupancy_rate) * 100, 1) AS avg_occupancy_pct,
            ROUND(AVG(review_scores_rating), 2) AS avg_rating,
            SUM(CASE WHEN instant_bookable THEN 1 ELSE 0 END) AS instant_bookable_count
        FROM listings
    """).fetchone()

    keys = ["total_listings", "total_neighbourhoods", "avg_price_usd",
            "median_price_usd", "avg_occupancy_pct", "avg_rating",
            "instant_bookable_count"]
    return dict(zip(keys, row))


def print_report(con: duckdb.DuckDBPyConnection) -> None:
    summary = market_summary(con)
    print("\n── Market Summary ───────────────────────────────")
    print(f"  Total listings        : {summary['total_listings']:,}")
    print(f"  Neighbourhoods        : {summary['total_neighbourhoods']}")
    print(f"  Avg nightly price     : ${summary['avg_price_usd']:.2f}")
    print(f"  Median nightly price  : ${summary['median_price_usd']:.2f}")
    print(f"  Avg occupancy         : {summary['avg_occupancy_pct']}%")
    print(f"  Avg rating            : {summary['avg_rating']}")
    print(f"  Instant bookable      : {summary['instant_bookable_count']:,}")

    print("\n── Avg Price by Neighbourhood (Top 10) ──────────")
    nbhd = avg_price_by_neighbourhood(con).head(10)
    for row in nbhd.iter_rows(named=True):
        print(f"  {row['neighbourhood']:<30} ${row['avg_price_usd']:>7.2f}  "
              f"({row['total_listings']} listings)")

    print("\n── Price & Occupancy by Room Type ───────────────")
    rt = price_by_room_type(con)
    for row in rt.iter_rows(named=True):
        print(f"  {row['room_type']:<25} ${row['avg_price_usd']:>7.2f}  "
              f"occ: {row['avg_occupancy_pct']}%")
