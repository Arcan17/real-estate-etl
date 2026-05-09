"""
Streamlit dashboard for Real Estate ETL Pipeline — Santiago, Chile.
Run: streamlit run dashboard.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import duckdb
from pathlib import Path

from load import DB_PATH, get_connection

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Real Estate Dashboard — Santiago",
    page_icon="🏢",
    layout="wide",
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_con():
    if not DB_PATH.exists():
        st.error("No data found. Run `python src/main.py` first.")
        st.stop()
    return get_connection(DB_PATH)


@st.cache_data
def load_listings():
    con = get_con()
    return pl.from_arrow(con.execute("SELECT * FROM listings").arrow())


con = get_con()
df = load_listings()

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.title("🔍 Filtros")

comunas = ["Todas"] + sorted(df["comuna"].drop_nulls().unique().to_list())
selected_comuna = st.sidebar.selectbox("Comuna", comunas)

price_min, price_max = int(df["price_clp"].min()), int(df["price_clp"].max())
price_range = st.sidebar.slider(
    "Precio mensual (CL$)",
    min_value=price_min,
    max_value=price_max,
    value=(price_min, price_max),
    step=10_000,
    format="%d",
)

bedrooms_options = ["Todos"] + sorted(
    [str(b) for b in df["bedrooms"].drop_nulls().unique().to_list()]
)
selected_bedrooms = st.sidebar.selectbox("Dormitorios", bedrooms_options)

# Apply filters
filtered = df.filter(
    (pl.col("price_clp") >= price_range[0]) &
    (pl.col("price_clp") <= price_range[1])
)
if selected_comuna != "Todas":
    filtered = filtered.filter(pl.col("comuna") == selected_comuna)
if selected_bedrooms != "Todos":
    filtered = filtered.filter(pl.col("bedrooms") == int(selected_bedrooms))

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏢 Real Estate Dashboard — Santiago, Chile")
st.caption("Datos scrapeados en tiempo real desde Portal Inmobiliario · ETL con Polars + DuckDB")

# ── KPI cards ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
if len(filtered) == 0:
    st.warning("No hay listings con los filtros seleccionados. Ajusta los filtros.")
    st.stop()

avg_price = filtered['price_clp'].mean()
median_price = filtered['price_clp'].median()
avg_sqm = filtered['sqm'].drop_nulls().mean()

col1.metric("Total listings", f"{len(filtered):,}")
col2.metric("Precio promedio", f"CL${avg_price:,.0f}" if avg_price else "—")
col3.metric("Precio mediano", f"CL${median_price:,.0f}" if median_price else "—")
col4.metric("Superficie prom.", f"{avg_sqm:.0f} m²" if avg_sqm else "—")
col5.metric("Comunas", f"{filtered['comuna'].drop_nulls().n_unique()}")

st.divider()

# ── Charts row 1 ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📍 Precio promedio por Comuna")
    by_comuna = (
        filtered
        .filter(pl.col("comuna").is_not_null() & (pl.col("comuna") != ""))
        .group_by("comuna")
        .agg([
            pl.count("price_clp").alias("total"),
            pl.mean("price_clp").alias("avg_price"),
        ])
        .filter(pl.col("total") >= 2)
        .sort("avg_price", descending=True)
        .head(12)
    )
    fig = px.bar(
        by_comuna.to_pandas(),
        x="avg_price", y="comuna",
        orientation="h",
        color="avg_price",
        color_continuous_scale="Teal",
        labels={"avg_price": "Precio Promedio (CL$)", "comuna": ""},
        text=by_comuna["avg_price"].map_elements(lambda x: f"${x:,.0f}", return_dtype=pl.String).to_list(),
    )
    fig.update_layout(
        coloraxis_showscale=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=0, r=0, t=10, b=0),
        height=380,
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🛏️ Precio por N° Dormitorios")
    by_bed = (
        filtered
        .filter(pl.col("bedrooms").is_not_null() & pl.col("bedrooms").is_between(1, 5))
        .group_by("bedrooms")
        .agg([
            pl.count("price_clp").alias("total"),
            pl.mean("price_clp").alias("avg_price"),
            pl.mean("sqm").alias("avg_sqm"),
        ])
        .sort("bedrooms")
    )
    fig2 = px.bar(
        by_bed.to_pandas(),
        x="bedrooms", y="avg_price",
        color="avg_price",
        color_continuous_scale="Teal",
        labels={"bedrooms": "Dormitorios", "avg_price": "Precio Promedio (CL$)"},
        text=by_bed["avg_price"].map_elements(lambda x: f"${x:,.0f}", return_dtype=pl.String).to_list(),
    )
    fig2.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=10, b=0),
        height=380,
    )
    fig2.update_traces(textposition="outside")
    st.plotly_chart(fig2, use_container_width=True)

# ── Charts row 2 ─────────────────────────────────────────────────────────────
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("💰 Distribución de Precios")
    fig3 = px.histogram(
        filtered.to_pandas(),
        x="price_clp",
        nbins=30,
        color_discrete_sequence=["#048A81"],
        labels={"price_clp": "Precio mensual (CL$)", "count": "N° listings"},
    )
    fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig3, use_container_width=True)

with col_right2:
    st.subheader("🏷️ Distribución por Presupuesto")
    by_budget = (
        filtered
        .group_by("budget_category")
        .agg(pl.count("price_clp").alias("total"))
        .sort("total", descending=True)
    )
    fig4 = px.pie(
        by_budget.to_pandas(),
        names="budget_category",
        values="total",
        color_discrete_sequence=px.colors.sequential.Teal,
        hole=0.4,
    )
    fig4.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig4, use_container_width=True)

# ── Data table ────────────────────────────────────────────────────────────────
st.divider()
st.subheader(f"📋 Listings ({len(filtered):,} resultados)")

display_df = (
    filtered
    .select(["title", "comuna", "bedrooms", "bathrooms", "sqm", "price_clp", "price_uf", "budget_category", "url"])
    .rename({
        "title": "Título", "comuna": "Comuna",
        "bedrooms": "Dorm.", "bathrooms": "Baños",
        "sqm": "m²", "price_clp": "Precio (CL$)",
        "price_uf": "Precio (UF)", "budget_category": "Categoría",
        "url": "Link",
    })
    .sort("Precio (CL$)")
)

st.dataframe(
    display_df.to_pandas(),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Precio (CL$)": st.column_config.NumberColumn(format="CL$%d"),
        "Precio (UF)": st.column_config.NumberColumn(format="%.1f UF"),
        "Link": st.column_config.LinkColumn(
            "Link",
            display_text="Ver en Portal Inmobiliario",
        ),
    }
)

# ── Export buttons ────────────────────────────────────────────────────────────
st.divider()
st.subheader("⬇️ Exportar datos")
col_csv, col_xlsx, _ = st.columns([1, 1, 3])

with col_csv:
    csv_bytes = display_df.write_csv().encode("utf-8")
    st.download_button(
        label="📄 Descargar CSV",
        data=csv_bytes,
        file_name="listings_santiago.csv",
        mime="text/csv",
    )

with col_xlsx:
    import io
    xlsx_buffer = io.BytesIO()
    display_df.to_pandas().to_excel(xlsx_buffer, index=False, sheet_name="Listings")
    xlsx_buffer.seek(0)
    st.download_button(
        label="📊 Descargar Excel",
        data=xlsx_buffer.getvalue(),
        file_name="listings_santiago.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
