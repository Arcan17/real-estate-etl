"""
Extract: scrapes real property listings from Portal Inmobiliario (Chile)
using Scrapling — an adaptive scraping framework with anti-bot capabilities.

Source: https://www.portalinmobiliario.com (public listings)
"""
import time
import random
import polars as pl
from pathlib import Path
from scrapling.fetchers import Fetcher

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_FILE = RAW_DIR / "listings_raw.csv"

BASE_URL = "https://www.portalinmobiliario.com/arriendo/departamento/santiago-metropolitana"
MAX_PAGES = 5  # ~240 listings per run (48 per page)


def _parse_card(card):
    """Extract fields from a single listing card."""
    try:
        title = card.css_first('.poly-component__title')
        price_el = card.css_first('.andes-money-amount__fraction')
        location = card.css_first('.poly-component__location')
        attrs = card.css('li')

        if not price_el:
            return None

        price_raw = price_el.text.replace('.', '').replace(',', '').strip()
        try:
            price = float(price_raw)
        except ValueError:
            return None

        # Parse location — "Street 123, Barrio, Comuna"
        loc_text = location.text.strip() if location else ""
        loc_parts = [p.strip() for p in loc_text.split(',')]
        neighbourhood = loc_parts[1] if len(loc_parts) > 1 else ""
        comuna = loc_parts[2] if len(loc_parts) > 2 else ""

        # Parse attributes list: bedrooms, bathrooms, sqm
        bedrooms = bathrooms = sqm = None
        for attr in attrs:
            t = attr.text.lower()
            if 'dormitorio' in t or 'dorm' in t:
                # "2 dormitorios" or "1 a 2 dormitorios" → take first number
                import re
                nums = re.findall(r'\d+', t)
                if nums:
                    bedrooms = int(nums[0])
            elif 'baño' in t or 'bath' in t:
                import re
                nums = re.findall(r'\d+', t)
                if nums:
                    bathrooms = int(nums[0])
            elif 'm²' in t or 'm2' in t:
                import re
                nums = re.findall(r'\d+', t)
                if nums:
                    sqm = int(nums[0])

        # URL — clean tracking params
        link = card.css_first('a')
        url = link.attrib.get('href', '').split('#')[0] if link else ""
        if url and not url.startswith('http'):
            url = 'https://' + url.lstrip('/')

        return {
            "title": title.text.strip() if title else "",
            "price_clp": price,
            "neighbourhood": neighbourhood,
            "comuna": comuna,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "sqm": sqm,
            "location_full": loc_text,
            "url": url,
        }
    except Exception:
        return None


def scrape_page(url: str) -> list[dict]:
    """Scrape one page of listings."""
    page = Fetcher.get(url, stealthy_headers=True)
    cards = page.css('.ui-search-result__wrapper')
    results = []
    for card in cards:
        row = _parse_card(card)
        if row:
            results.append(row)
    return results


def scrape(max_pages: int = MAX_PAGES, force: bool = False) -> pl.DataFrame:
    """Scrape multiple pages and return a Polars DataFrame."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if RAW_FILE.exists() and not force:
        print(f"  Already exists: {RAW_FILE.name} — loading from cache")
        return pl.read_csv(RAW_FILE)

    all_rows = []
    for page_num in range(max_pages):
        offset = page_num * 48
        url = f"{BASE_URL}_Desde_{offset + 1}" if offset > 0 else BASE_URL
        print(f"  Scraping page {page_num + 1}/{max_pages} ({len(all_rows)} listings so far)...")
        rows = scrape_page(url)
        all_rows.extend(rows)
        if page_num < max_pages - 1:
            time.sleep(random.uniform(1.5, 3.0))  # polite delay

    df = pl.DataFrame(all_rows)
    df.write_csv(RAW_FILE)
    print(f"  Saved: {RAW_FILE.name} ({len(df):,} rows)")
    return df


def download_data(dest: Path = RAW_FILE, force: bool = False, **kwargs) -> Path:
    """Compatibility wrapper for main.py."""
    scrape(force=force)
    return dest


if __name__ == "__main__":
    df = scrape(force=True)
    print(df.head(10))
