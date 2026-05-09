"""
Extract: generates realistic Airbnb-style listings data for Santiago, Chile.
Simulates what a real scraper/API client would produce from sources like
Inside Airbnb, Portal Inmobiliario, or government open data registries.
"""
import random
import numpy as np
import polars as pl
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_FILE = RAW_DIR / "listings_raw.csv"

NEIGHBOURHOODS = [
    "Providencia", "Las Condes", "Ñuñoa", "Santiago Centro",
    "Vitacura", "Miraflores", "La Reina", "San Miguel",
    "Macul", "Lo Barnechea", "Peñalolén", "La Florida",
    "Estación Central", "Recoleta", "Independencia",
]

ROOM_TYPES = [
    "Entire home/apt", "Entire home/apt", "Entire home/apt",  # weighted higher
    "Private room", "Private room",
    "Shared room",
    "Hotel room",
]

PRICE_BY_NEIGHBOURHOOD = {
    "Vitacura": (120, 50), "Las Condes": (100, 40), "Lo Barnechea": (95, 35),
    "Providencia": (85, 30), "La Reina": (80, 28), "Ñuñoa": (70, 25),
    "Miraflores": (75, 25), "Santiago Centro": (60, 20), "San Miguel": (55, 18),
    "La Florida": (50, 15), "Macul": (50, 15), "Peñalolén": (48, 14),
    "Recoleta": (55, 18), "Independencia": (52, 16), "Estación Central": (45, 12),
}

PRICE_MULTIPLIER_BY_ROOM = {
    "Entire home/apt": 1.0, "Hotel room": 0.9,
    "Private room": 0.45, "Shared room": 0.25,
}

BATHROOM_OPTIONS = ["1 bath", "1 bath", "1.5 baths", "2 baths", "Shared half-bath"]

NAMES = [
    "Cozy {room} in {nbhd}", "Modern {room} near Parque Balmaceda",
    "Bright {room} in the heart of {nbhd}", "Charming studio in {nbhd}",
    "Stylish {room} with city views", "Comfortable {room} - great location",
    "Brand new {room} in {nbhd}", "Spacious {room} close to metro",
]


def generate_listings(n: int = 1500, seed: int = 42) -> pl.DataFrame:
    """Generate n synthetic property listings for Santiago, Chile."""
    random.seed(seed)
    np.random.seed(seed)

    rows = []
    for i in range(1, n + 1):
        nbhd = random.choice(NEIGHBOURHOODS)
        room_type = random.choice(ROOM_TYPES)
        mu, sigma = PRICE_BY_NEIGHBOURHOOD[nbhd]
        base_price = max(10.0, np.random.normal(mu, sigma))
        price = round(base_price * PRICE_MULTIPLIER_BY_ROOM[room_type], 2)

        bedrooms = random.choice([1, 1, 1, 2, 2, 3, None])
        if room_type in ("Shared room", "Private room"):
            bedrooms = 1

        rating = None
        n_reviews = random.randint(0, 200)
        if n_reviews >= 3:
            rating = round(min(5.0, max(3.0, np.random.normal(4.6, 0.3))), 2)

        name_tpl = random.choice(NAMES)
        name = name_tpl.format(
            room="apartment" if room_type == "Entire home/apt" else "room",
            nbhd=nbhd,
        )

        # Santiago coordinates with small jitter per neighbourhood
        lat_base = -33.45 + NEIGHBOURHOODS.index(nbhd) * 0.01
        lon_base = -70.65 + NEIGHBOURHOODS.index(nbhd) * 0.01
        lat = lat_base + np.random.uniform(-0.02, 0.02)
        lon = lon_base + np.random.uniform(-0.02, 0.02)

        rows.append({
            "id": i,
            "name": name,
            "neighbourhood_cleansed": nbhd,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "room_type": room_type,
            "accommodates": str(random.randint(1, 8)),
            "bedrooms": str(bedrooms) if bedrooms else None,
            "bathrooms_text": random.choice(BATHROOM_OPTIONS),
            "price": f"${price:,.2f}",
            "minimum_nights": str(random.choice([1, 1, 2, 3, 7])),
            "maximum_nights": str(random.choice([30, 60, 90, 365])),
            "number_of_reviews": str(n_reviews),
            "review_scores_rating": str(rating) if rating else None,
            "availability_365": str(random.randint(0, 365)),
            "instant_bookable": random.choice(["t", "t", "f"]),
        })

    return pl.DataFrame(rows)


def download_data(dest: Path = RAW_FILE, force: bool = False, n: int = 1500) -> Path:
    """Generate synthetic listings and save as compressed CSV."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force:
        print(f"  Already exists: {dest.name} ({dest.stat().st_size / 1024:.0f} KB)")
        return dest

    print(f"  Generating {n:,} synthetic listings for Santiago, Chile...")
    df = generate_listings(n=n)
    df.write_csv(dest)
    print(f"  Saved: {dest.name} ({dest.stat().st_size / 1024:.0f} KB, {len(df):,} rows)")
    return dest


if __name__ == "__main__":
    download_data(force=True)
