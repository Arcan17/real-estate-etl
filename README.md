# Real Estate ETL Pipeline + Dashboard

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Polars](https://img.shields.io/badge/Polars-0.20+-CD792C?style=flat)
![DuckDB](https://img.shields.io/badge/DuckDB-0.10+-FFC832?style=flat)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat&logo=streamlit)
![CI](https://img.shields.io/github/actions/workflow/status/Arcan17/real-estate-etl/ci.yml?label=CI&logo=github)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

A Python ETL pipeline that scrapes real property listings from **Portal Inmobiliario Chile**, cleans and standardizes the data with **Polars**, loads it into **DuckDB**, and visualizes market insights in an interactive **Streamlit** dashboard.

---

## What it does

1. **Scrapes** live property listings from Portal Inmobiliario using [Scrapling](https://github.com/D4Vinci/Scrapling) — an adaptive scraping framework with anti-bot capabilities
2. **Transforms** raw data with Polars: parses prices, bedrooms, m², computes UF price, budget category, price per m²
3. **Loads** clean data into DuckDB for fast analytical SQL queries
4. **Visualizes** market insights in a Streamlit dashboard with filters, charts, and clickable links to each property

---

## Pipeline

```
Portal Inmobiliario (live scrape)
        │  Scrapling — stealthy HTTP, adaptive selectors
        ▼
  extract.py    ← 5 pages × 48 listings = ~240 properties
        │
        ▼
  transform.py  ← Polars: clean, validate, enrich
        │  - parse price strings (CL$363.000 → 363000.0)
        │  - parse bedrooms/bathrooms/sqm from text
        │  - drop rows outside business rules
        │  - add: price_uf, price_per_sqm, budget_category, url
        ▼
  load.py       ← DuckDB: schema + bulk insert
        │
        ▼
  analytics.py  ← SQL: avg by comuna, by bedrooms, budget distribution
        │
        ▼
  dashboard.py  ← Streamlit: interactive filters + Plotly charts
```

---

## Sample output

```
── Market Summary — Arriendos Santiago ──────────
  Total listings    : 237
  Comunas           : 19
  Precio promedio   : CL$363,214 (9.6 UF)
  Precio mediano    : CL$341,000
  Superficie prom.  : 37 m²
  Rango precios     : CL$224,000 – CL$770,000

── Precio por N° Dormitorios ─────────────────────
  1 dorm.   CL$   325,701   31 m²
  2 dorm.   CL$   417,323   46 m²
  3 dorm.   CL$   558,125   69 m²
```

---

## Quickstart

```bash
git clone https://github.com/Arcan17/real-estate-etl.git
cd real-estate-etl

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Run the ETL pipeline (scrapes live data)
python src/main.py

# Launch the dashboard
streamlit run dashboard.py
```

Open **http://localhost:8501** in your browser.

---

## Running tests

```bash
pytest tests/ -v
# 16 passed
```

---

## Project structure

```
real-estate-etl/
├── src/
│   ├── extract.py      # Scrapling scraper — Portal Inmobiliario
│   ├── transform.py    # Polars transformations and business rules
│   ├── load.py         # DuckDB schema creation and bulk load
│   ├── analytics.py    # SQL market analytics queries
│   └── main.py         # Pipeline orchestrator
├── dashboard.py        # Streamlit interactive dashboard
├── tests/
│   └── test_transform.py   # 16 unit tests
├── requirements.txt
└── .github/workflows/ci.yml
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Scraping | Scrapling 0.4+ (adaptive, anti-bot) |
| Data transformation | Polars 0.20+ |
| Analytical database | DuckDB 0.10+ |
| Dashboard | Streamlit + Plotly |
| Columnar format | Apache Parquet |
| Testing | pytest |
| CI/CD | GitHub Actions |

---

## License

MIT
