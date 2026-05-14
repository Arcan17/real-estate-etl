#!/bin/bash
# Startup script for Railway deployment.
# Seeds demo data if the DB doesn't exist, then launches the Streamlit dashboard.

set -e

DB_PATH="data/listings.duckdb"

mkdir -p data

if [ ! -f "$DB_PATH" ]; then
    echo "[start.sh] No database found. Seeding demo data..."
    python scripts/seed_demo.py
    echo "[start.sh] Demo data ready."
else
    echo "[start.sh] Database found at $DB_PATH"
fi

echo "[start.sh] Starting Streamlit dashboard..."
exec streamlit run dashboard.py \
    --server.port="${PORT:-8501}" \
    --server.address=0.0.0.0 \
    --server.headless=true
