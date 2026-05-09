"""
Orchestrates the full ETL pipeline:
  Extract → Transform → Load → Analytics
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from extract import download_data, RAW_FILE
from transform import load_raw, clean, save_parquet
from load import load_pipeline, DB_PATH
from analytics import print_report

PROCESSED_FILE = Path(__file__).parent.parent / "data" / "processed" / "listings_clean.parquet"


def main():
    print("=" * 52)
    print("  Real Estate ETL Pipeline — Santiago, Chile")
    print("  Source: Portal Inmobiliario Chile (portalinmobiliario.com)")
    print("=" * 52)

    # 1. Extract
    print("\n[1/4] Extract")
    download_data(dest=RAW_FILE)

    # 2. Transform
    print("\n[2/4] Transform")
    df_raw = load_raw(RAW_FILE)
    print(f"  Raw rows     : {len(df_raw):,}")
    df_clean = clean(df_raw)
    print(f"  Clean rows   : {len(df_clean):,}")
    print(f"  Columns      : {df_clean.columns}")
    save_parquet(df_clean, PROCESSED_FILE)

    # 3. Load
    print("\n[3/4] Load → DuckDB")
    con = load_pipeline(df_clean, DB_PATH)

    # 4. Analytics
    print("\n[4/4] Analytics")
    print_report(con)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
