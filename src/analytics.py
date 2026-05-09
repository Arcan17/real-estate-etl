"""
Analytics: SQL queries on DuckDB to extract market insights from real listings.
"""
import duckdb
import polars as pl


def avg_price_by_comuna(con: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    return pl.from_arrow(con.execute("""
        SELECT
            comuna,
            COUNT(*)                        AS total,
            ROUND(AVG(price_clp), 0)        AS avg_price_clp,
            ROUND(MEDIAN(price_clp), 0)     AS median_price_clp,
            ROUND(AVG(price_uf), 1)         AS avg_price_uf
        FROM listings
        WHERE comuna != 'Unknown' AND comuna != ''
        GROUP BY comuna
        HAVING COUNT(*) >= 3
        ORDER BY avg_price_clp DESC
        LIMIT 15
    """).arrow())


def price_by_bedrooms(con: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    return pl.from_arrow(con.execute("""
        SELECT
            bedrooms,
            COUNT(*)                    AS total,
            ROUND(AVG(price_clp), 0)    AS avg_price_clp,
            ROUND(AVG(price_uf), 1)     AS avg_price_uf,
            ROUND(AVG(sqm), 0)          AS avg_sqm
        FROM listings
        WHERE bedrooms IS NOT NULL AND bedrooms BETWEEN 1 AND 5
        GROUP BY bedrooms
        ORDER BY bedrooms
    """).arrow())


def budget_distribution(con: duckdb.DuckDBPyConnection) -> pl.DataFrame:
    return pl.from_arrow(con.execute("""
        SELECT
            budget_category,
            COUNT(*)                                        AS total,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
        FROM listings
        GROUP BY budget_category
        ORDER BY MIN(price_clp)
    """).arrow())


def market_summary(con: duckdb.DuckDBPyConnection) -> dict:
    row = con.execute("""
        SELECT
            COUNT(*)                        AS total_listings,
            COUNT(DISTINCT comuna)          AS total_comunas,
            ROUND(AVG(price_clp), 0)        AS avg_price_clp,
            ROUND(MEDIAN(price_clp), 0)     AS median_price_clp,
            ROUND(AVG(price_uf), 1)         AS avg_price_uf,
            ROUND(AVG(sqm), 0)              AS avg_sqm,
            MIN(price_clp)                  AS min_price_clp,
            MAX(price_clp)                  AS max_price_clp
        FROM listings
    """).fetchone()
    keys = ["total_listings", "total_comunas", "avg_price_clp", "median_price_clp",
            "avg_price_uf", "avg_sqm", "min_price_clp", "max_price_clp"]
    return dict(zip(keys, row))


def print_report(con: duckdb.DuckDBPyConnection) -> None:
    s = market_summary(con)
    print("\n── Market Summary — Arriendos Santiago ──────────")
    print(f"  Total listings    : {s['total_listings']:,}")
    print(f"  Comunas           : {s['total_comunas']}")
    print(f"  Precio promedio   : CL${s['avg_price_clp']:,.0f} ({s['avg_price_uf']} UF)")
    print(f"  Precio mediano    : CL${s['median_price_clp']:,.0f}")
    print(f"  Superficie prom.  : {s['avg_sqm']} m²")
    print(f"  Rango precios     : CL${s['min_price_clp']:,.0f} – CL${s['max_price_clp']:,.0f}")

    print("\n── Precio promedio por Comuna (Top 10) ──────────")
    for row in avg_price_by_comuna(con).head(10).iter_rows(named=True):
        print(f"  {row['comuna']:<30} CL${row['avg_price_clp']:>10,.0f}  ({row['total']} listings)")

    print("\n── Precio por N° Dormitorios ─────────────────────")
    for row in price_by_bedrooms(con).iter_rows(named=True):
        print(f"  {row['bedrooms']} dorm.   CL${row['avg_price_clp']:>10,.0f}   {row['avg_sqm']} m²")

    print("\n── Distribución por Presupuesto ─────────────────")
    for row in budget_distribution(con).iter_rows(named=True):
        print(f"  {row['budget_category']:<12}  {row['pct']:>5.1f}%  ({row['total']} listings)")
