# Real Estate ETL Pipeline

**End-to-end data pipeline for Chilean real estate market intelligence.**

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Polars](https://img.shields.io/badge/Polars-0.20+-CD792C?style=flat)
![DuckDB](https://img.shields.io/badge/DuckDB-0.10+-FFC832?style=flat)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat&logo=streamlit)
![Tests](https://img.shields.io/badge/tests-45%20passing-brightgreen?style=flat)
![CI](https://img.shields.io/github/actions/workflow/status/Arcan17/real-estate-etl/ci.yml?label=CI&logo=github)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)
![Live Demo](https://img.shields.io/badge/demo-live-brightgreen?style=flat)

**🚀 [Live Demo](https://real-estate-etl-production.up.railway.app)**

---

## The Problem

Searching for rental properties in Santiago, Chile means opening dozens of tabs, comparing prices manually, and having no way to answer basic questions like:

- What's the average price per m² in Providencia vs Ñuñoa?
- Which listings are priced below the commune average?
- How do prices change across bedroom counts?

There's no clean API, no structured data, and no way to export or analyze listings at scale.

## The Solution

This pipeline scrapes live listings from **Portal Inmobiliario**, cleans and enriches the data with **Polars**, stores it in **DuckDB**, and serves it through a **Streamlit dashboard** and **FastAPI REST API** — with CSV/Excel export included.

One command fetches ~240 live listings, transforms them into structured market intelligence, and makes them queryable and downloadable in minutes.

---

## Dashboard

![Dashboard](docs/screenshots/dashboard.png)

---

## Features

- **Live scraping** of ~240 property listings with Scrapling (anti-bot fingerprinting, adaptive selectors)
- **Data normalization**: parses price strings, extracts bedrooms/bathrooms/m², computes UF price and price per m²
- **Analytical queries**: average price by commune, by bedroom count, budget distribution
- **Interactive dashboard**: filters by commune, bedrooms, price range — with Plotly charts and clickable property links
- **One-click export**: CSV and Excel (.xlsx) from dashboard and REST API
- **FastAPI REST API**: paginated listings, summary stats, per-commune analytics, file export
- **pytest suite**: ETL unit tests + API endpoint tests (including data-quality and Query validation)
- **Docker Compose**: pipeline, dashboard, and API as separate services
- **GitHub Actions CI/CD**: runs on every push

---

## Pipeline Architecture

```
Portal Inmobiliario (live)
        │
        │  Scrapling — stealthy HTTP, adaptive selectors
        ▼
  extract.py        ~240 listings across 5 pages
        │
        ▼
  transform.py      Polars: clean, validate, enrich
        │           ├─ parse price strings (CL$363.000 → 363000.0)
        │           ├─ extract bedrooms/bathrooms/m² from text
        │           ├─ compute price_uf, price_per_sqm
        │           └─ assign budget_category (budget/mid/premium)
        ▼
  load.py           DuckDB: schema + bulk insert
        │
        ▼
  analytics.py      SQL: market summary, per-commune, per-bedroom stats
        │
        ├──► dashboard.py     Streamlit: interactive UI + export
        └──► api.py           FastAPI: REST endpoints + file download
```

---

## Sample Output

```
── Market Summary — Arriendos Santiago ──────────────
  Total listings    : 237
  Comunas           : 19
  Precio promedio   : CL$363,214  (9.6 UF)
  Precio mediano    : CL$341,000
  Superficie prom.  : 37 m²
  Rango de precios  : CL$224,000 – CL$770,000

── Precio por N° Dormitorios ────────────────────────
  1 dorm.   CL$  325,701   31 m²
  2 dorm.   CL$  417,323   46 m²
  3 dorm.   CL$  558,125   69 m²
```

---

## Tech Stack

| Layer            | Technology                              |
|------------------|-----------------------------------------|
| Scraping         | Scrapling 0.4+ (adaptive, anti-bot)     |
| Transformation   | Polars 0.20+                            |
| Analytical DB    | DuckDB 0.10+                            |
| Dashboard        | Streamlit + Plotly                      |
| REST API         | FastAPI + Uvicorn                       |
| Export           | openpyxl (Excel), csv (stdlib)          |
| Containerization | Docker + Docker Compose                 |
| Testing          | pytest suite                            |
| CI/CD            | GitHub Actions                          |

---

## Local Setup

```bash
# 1. Clone and install
git clone https://github.com/Arcan17/real-estate-etl.git
cd real-estate-etl

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Run the ETL pipeline (scrapes live data — takes ~30 seconds)
python -m src.main

# 3. Launch the dashboard
streamlit run dashboard.py
# Open http://localhost:8501

# 4. Launch the REST API (optional)
uvicorn src.api:app --reload
# Docs at http://localhost:8000/docs
```

---

## Environment Variables

No API keys required. The scraper targets a public website. Copy the example file if you want to override defaults:

```bash
cp .env.example .env
```

| Variable        | Description                        | Default                     |
|-----------------|------------------------------------|-----------------------------|
| `DB_PATH`       | Path to the DuckDB database file   | `data/listings.duckdb`      |
| `MAX_PAGES`     | Number of pages to scrape          | `5`                         |
| `LOG_LEVEL`     | Logging verbosity                  | `INFO`                      |

---

## REST API

![API Docs](docs/screenshots/api-docs.png)

```bash
uvicorn src.api:app --reload
# Interactive docs: http://localhost:8000/docs
```

| Method | Endpoint                    | Description                            |
|--------|-----------------------------|----------------------------------------|
| `GET`  | `/api/health`               | Health check + DB status               |
| `GET`  | `/api/listings`             | Paginated listings with filters        |
| `GET`  | `/api/summary`              | Market summary stats                   |
| `GET`  | `/api/comunas`              | All communes with avg price            |
| `GET`  | `/api/prices/by-comuna`     | Avg price per commune                  |
| `GET`  | `/api/prices/by-bedrooms`   | Avg price by bedroom count             |
| `GET`  | `/api/data-quality`         | Dataset completeness and quality report |
| `GET`  | `/api/export/csv`           | Download all listings as CSV           |
| `GET`  | `/api/export/excel`         | Download all listings as Excel (.xlsx) |

```bash
# Example queries
curl "http://localhost:8000/api/summary"
curl "http://localhost:8000/api/listings?comuna=Providencia&bedrooms=2&limit=20"
curl "http://localhost:8000/api/data-quality"
curl "http://localhost:8000/api/export/csv" -o listings.csv
curl "http://localhost:8000/api/export/excel" -o listings.xlsx
```

### Data quality

`GET /api/data-quality` returns a completeness and integrity report for the current dataset:

```json
{
  "rows_total": 237,
  "missing_bedrooms": 12,
  "missing_bathrooms": 8,
  "missing_sqm": 21,
  "duplicate_urls": 0,
  "min_price_clp": 224000,
  "max_price_clp": 770000,
  "avg_price_clp": 363214,
  "generated_at": "2024-05-25T20:00:00+00:00"
}
```

<details>
<summary>Sample JSON — <code>/api/summary</code></summary>

```json
{
  "total_listings": 237,
  "comunas": 19,
  "avg_price_clp": 363214,
  "median_price_clp": 341000,
  "avg_sqm": 37.2,
  "min_price_clp": 224000,
  "max_price_clp": 770000
}
```
</details>

---

## Docker

```bash
# Run the ETL pipeline
docker compose --profile pipeline run pipeline

# Launch the Streamlit dashboard
docker compose up dashboard

# Launch the FastAPI REST API
docker compose --profile api up api
```

---

## Running Tests

```bash
pytest tests/ -v --tb=short
```

```
tests/test_transform.py   ← ETL transformation logic
tests/test_api.py         ← API endpoints, filters, data-quality, Query validation
─────────────────────────────────────
55 passed
```

---

## Project Structure

```
real-estate-etl/
├── src/
│   ├── extract.py        # Scrapling scraper — Portal Inmobiliario
│   ├── transform.py      # Polars ETL: cleaning, validation, enrichment
│   ├── load.py           # DuckDB schema + bulk insert
│   ├── analytics.py      # SQL market analytics queries
│   ├── main.py           # Pipeline orchestrator (E → T → L → A)
│   └── api.py            # FastAPI REST API
├── dashboard.py          # Streamlit interactive dashboard
├── tests/
│   ├── test_transform.py # ETL unit tests
│   └── test_api.py       # API endpoint tests
├── docs/
│   └── screenshots/
├── data/                 # DuckDB database (gitignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── .github/workflows/ci.yml
```

---

## Technical Decisions

**Why Scrapling over BeautifulSoup or Playwright?**
Scrapling uses adaptive CSS selectors and stealthy HTTP fingerprinting, which makes it more resilient to anti-bot protections than raw BS4 and faster/lighter than browser automation with Playwright. For a pipeline that runs daily, reliability matters more than flexibility.

**Why DuckDB over PostgreSQL?**
DuckDB is serverless, zero-config, and blazing fast for analytical queries on local data. For a pipeline that reads far more than it writes, and doesn't need concurrent writes, DuckDB eliminates the overhead of running a server while delivering full SQL + Parquet support.

**Why Polars over pandas?**
Polars is significantly faster for columnar transformations, has a cleaner API with strict typing, and produces better errors. For a scraping pipeline where data quality matters, Polars' strict schema enforcement catches problems early.

---

## Current limitations

- **DOM dependency**: the scraper relies on Portal Inmobiliario's current CSS selectors — any redesign of the site will require selector updates
- **Geography**: dataset covers Santiago rental listings only; other Chilean cities or sale listings would need additional configuration
- **UF conversion**: price-to-UF conversion uses a static approximation hardcoded at pipeline run time; a production system should call the official CMF/SII UF API for the exact daily value
- **No incremental loading**: each pipeline run replaces all data (no deduplication by listing ID)
- **No authentication**: the REST API is read-only over public data, acceptable for portfolio use

---

## Production roadmap

- Scheduled ingestion (APScheduler or cron) with configurable run interval
- Historical price snapshots: store each run with timestamp for trend analysis
- Configurable commune and property-type targets via environment variables
- Real UF conversion via CMF/SII API instead of static approximation
- Monitoring and alerting for scrape failures (Telegram or email)
- Retry/backoff strategy with proxy rotation for long-running scrapes
- Incremental loading with listing-ID deduplication to avoid data churn

---

## Use Cases

This project is directly adaptable for:

- **Real estate agencies** — automated market reports for agents
- **Property investors** — below-average price detection and opportunity ranking
- **Price monitoring** — daily tracking of specific communes or property types
- **Data consulting** — template for any scraping + ETL + dashboard engagement

---

## License

MIT
