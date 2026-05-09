# Real Estate ETL Pipeline

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Polars](https://img.shields.io/badge/Polars-0.20+-CD792C?style=flat)
![DuckDB](https://img.shields.io/badge/DuckDB-0.10+-FFC832?style=flat)
![CI](https://img.shields.io/github/actions/workflow/status/Arcan17/real-estate-etl/ci.yml?label=CI&logo=github)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

A Python ETL pipeline that extracts property listings data, cleans and standardizes it using **Polars**, loads it into a **DuckDB** analytical database, and generates market insights via SQL.

---

## The problem it solves

Real estate data comes from many fragmented sources — government registries, listing portals, open data APIs — each with inconsistent formats, currencies, null values, and naming conventions. This pipeline automates:

- **Extraction** from any source (CSV, API, scraper output)
- **Transformation**: type casting, business-rule validation, derived metrics
- **Loading** into an analytical database for fast SQL queries
- **Reporting**: market summary, price by neighbourhood/room type, value listings

---

## Pipeline

```
Source data (CSV / API)
        │
        ▼
  extract.py      ← load raw listings into memory
        │
        ▼
  transform.py    ← Polars: clean, validate, enrich
        │  - parse price strings ($1,234.00 → 1234.0)
        │  - parse bathroom text ("1.5 baths" → 1.5)
        │  - drop rows that violate business rules
        │  - add: price_per_bedroom, occupancy_rate, rating_category
        ▼
  load.py         ← DuckDB: schema creation + bulk insert
        │
        ▼
  analytics.py    ← SQL: market summary, rankings, value listings
```

---

## Sample output

```
── Market Summary ───────────────────────────────
  Total listings        : 1,500
  Neighbourhoods        : 15
  Avg nightly price     : $49.93
  Median nightly price  : $42.27
  Avg occupancy         : 50.2%
  Avg rating            : 4.6
  Instant bookable      : 995

── Avg Price by Neighbourhood (Top 10) ──────────
  Vitacura                        $  92.47  (102 listings)
  Las Condes                      $  71.64  (91 listings)
  Lo Barnechea                    $  67.88  (109 listings)
  Providencia                     $  64.58  (90 listings)
  ...

── Price & Occupancy by Room Type ───────────────
  Entire home/apt            $  69.46  occ: 49.6%
  Hotel room                 $  60.61  occ: 49.4%
  Private room               $  31.31  occ: 51.9%
  Shared room                $  16.70  occ: 49.3%
```

---

## Quickstart

```bash
git clone https://github.com/Arcan17/real-estate-etl.git
cd real-estate-etl

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

python src/main.py
```

To plug in your own data source, replace `extract.py` with your scraper or API client — `transform.py` and `load.py` are data-source agnostic.

---

## Running tests

```bash
pytest tests/ -v
```

```
tests/test_transform.py::test_parse_price_standard PASSED
tests/test_transform.py::test_parse_price_null_on_invalid PASSED
tests/test_transform.py::test_parse_bathrooms_whole PASSED
tests/test_transform.py::test_parse_bathrooms_half PASSED
tests/test_transform.py::test_parse_bathrooms_decimal PASSED
tests/test_transform.py::test_clean_returns_dataframe PASSED
...
16 passed in 0.08s
```

---

## Project structure

```
real-estate-etl/
├── src/
│   ├── extract.py      # Data extraction (CSV / API / scraper)
│   ├── transform.py    # Polars transformations and business rules
│   ├── load.py         # DuckDB schema creation and bulk load
│   ├── analytics.py    # SQL market analytics queries
│   └── main.py         # Pipeline orchestrator
├── tests/
│   └── test_transform.py   # 16 unit tests
├── requirements.txt
└── .github/workflows/ci.yml
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Data transformation | Polars 0.20+ |
| Analytical database | DuckDB 0.10+ |
| HTTP client | httpx |
| Columnar format | Apache Parquet (pyarrow) |
| Testing | pytest |
| CI/CD | GitHub Actions |

---

## License

MIT
