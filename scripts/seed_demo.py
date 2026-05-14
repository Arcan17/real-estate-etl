"""
Seed demo data for the Real Estate ETL Pipeline dashboard.
Generates ~240 realistic Santiago rental listings directly into DuckDB.
Run this when live scraping is not available (e.g. Railway deploy).
"""

import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import duckdb
import polars as pl
from pathlib import Path
from src.load import DB_PATH, get_connection, create_schema

random.seed(42)

# ── Santiago commune data ─────────────────────────────────────────────────────
COMUNAS = [
    ("Providencia",     "Barrio Italia"),
    ("Providencia",     "Pedro de Valdivia"),
    ("Providencia",     "Manuel Montt"),
    ("Ñuñoa",           "Irarrázaval"),
    ("Ñuñoa",           "Villa Frei"),
    ("Ñuñoa",           "Exequiel Fernández"),
    ("Las Condes",      "El Golf"),
    ("Las Condes",      "Manquehue"),
    ("Las Condes",      "Lo Barnechea"),
    ("Vitacura",        "Las Hualtatas"),
    ("Vitacura",        "Alonso de Córdova"),
    ("Santiago",        "Barrio Lastarria"),
    ("Santiago",        "Barrio Yungay"),
    ("Santiago",        "Barrio Brasil"),
    ("San Miguel",      "Gran Avenida"),
    ("San Miguel",      "Lo Ovalle"),
    ("La Florida",      "Vicuña Mackenna"),
    ("La Florida",      "Rojas Magallanes"),
    ("Maipú",           "Pudahuel Sur"),
    ("Maipú",           "El Bosque"),
    ("Recoleta",        "Barrio Bellavista"),
    ("Recoleta",        "Av. Recoleta"),
    ("Independencia",   "Av. Independencia"),
    ("Macul",           "Macul"),
    ("Peñalolén",       "San Luis"),
    ("La Reina",        "Av. Ossa"),
    ("Miraflores",      "Miraflores"),
    ("Pudahuel",        "Pudahuel"),
]

PROPERTY_TYPES = [
    "Departamento", "Apartamento", "Estudio", "Loft", "Suite"
]

# Price ranges by commune (CLP/month)
COMMUNE_PRICE = {
    "Vitacura":      (500_000, 770_000),
    "Las Condes":    (450_000, 700_000),
    "Providencia":   (380_000, 620_000),
    "La Reina":      (350_000, 550_000),
    "Ñuñoa":         (320_000, 520_000),
    "Miraflores":    (300_000, 480_000),
    "Santiago":      (260_000, 420_000),
    "Recoleta":      (250_000, 400_000),
    "San Miguel":    (250_000, 390_000),
    "Macul":         (240_000, 380_000),
    "La Florida":    (240_000, 370_000),
    "Peñalolén":     (230_000, 360_000),
    "Independencia": (230_000, 370_000),
    "Maipú":         (224_000, 340_000),
    "Pudahuel":      (224_000, 320_000),
}

# Bedrooms → typical sqm range
BEDROOM_SQM = {
    1: (25, 45),
    2: (42, 70),
    3: (65, 100),
}


def make_listing(idx: int) -> dict:
    comuna, neighbourhood = random.choice(COMUNAS)
    bedrooms = random.choices([1, 2, 3], weights=[40, 45, 15])[0]
    bathrooms = max(1, bedrooms - random.randint(0, 1))

    price_min, price_max = COMMUNE_PRICE.get(comuna, (240_000, 500_000))
    # bedrooms push price up
    price_min = int(price_min * (1 + (bedrooms - 1) * 0.25))
    price_max = int(price_max * (1 + (bedrooms - 1) * 0.25))
    price_clp = float(random.randint(price_min // 1000, price_max // 1000) * 1000)

    sqm_min, sqm_max = BEDROOM_SQM[bedrooms]
    sqm = random.randint(sqm_min, sqm_max)

    prop_type = random.choice(PROPERTY_TYPES)
    title = f"{prop_type} {bedrooms}D/{bathrooms}B en {neighbourhood}, {comuna}"

    price_per_sqm = round(price_clp / sqm, 1) if sqm > 0 else None
    price_uf = round(price_clp / 38_000, 2)

    if price_clp < 300_000:
        budget_category = "Económico"
    elif price_clp < 600_000:
        budget_category = "Medio"
    elif price_clp < 1_000_000:
        budget_category = "Premium"
    else:
        budget_category = "Lujo"

    url = f"https://www.portalinmobiliario.com/arriendo/departamento/{idx + 1000}-demo-{comuna.lower().replace(' ', '-')}"

    return {
        "title": title,
        "price_clp": price_clp,
        "neighbourhood": neighbourhood,
        "comuna": comuna,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "sqm": sqm,
        "location_full": f"{neighbourhood}, {comuna}, Santiago",
        "url": url,
        "price_per_sqm": price_per_sqm,
        "price_uf": price_uf,
        "budget_category": budget_category,
    }


def seed(n: int = 240) -> None:
    print(f"Seeding {n} demo listings into {DB_PATH}...")
    listings = [make_listing(i) for i in range(n)]
    df = pl.DataFrame(listings)

    con = get_connection(DB_PATH)
    create_schema(con)

    con.register("staging", df.to_arrow())
    cols = ", ".join(df.columns)
    con.execute(f"INSERT INTO listings ({cols}) SELECT {cols} FROM staging")
    count = con.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    print(f"  Seeded {count} listings OK → {DB_PATH}")
    con.close()


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    seed(n)
