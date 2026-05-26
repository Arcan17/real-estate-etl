"""
Centralised configuration — all tuneable values come from environment variables
with safe defaults so the project runs without any extra setup.
"""

import os

# ── Scraper ────────────────────────────────────────────────────────────────────

BASE_URL: str = os.getenv(
    "BASE_URL",
    "https://www.portalinmobiliario.com/arriendo/departamento/santiago-metropolitana",
)

MAX_PAGES: int = int(os.getenv("MAX_PAGES", "5"))

SCRAPE_DELAY_MIN: float = float(os.getenv("SCRAPE_DELAY_MIN", "1.5"))
SCRAPE_DELAY_MAX: float = float(os.getenv("SCRAPE_DELAY_MAX", "3.0"))

# ── API ────────────────────────────────────────────────────────────────────────

# Comma-separated list of allowed CORS origins.
# Defaults to "*" for local demo; set to your actual domain in production.
_cors_raw: str = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",")]
