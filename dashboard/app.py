"""Streamlit dashboard: mõõdetud vs Open-Meteo CAMS prognoos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from scripts.pipeline.db import get_conn

st.set_page_config(page_title="Õhukvaliteedi võrdlus", layout="wide")
st.title("Õhukvaliteet: mõõdetud vs CAMS prognoos")


def clean_formula(s: str) -> str:
    return s.replace("<sub>", "").replace("</sub>", "")


@st.cache_data(ttl=300)
def load_dims():
    with get_conn() as conn:
        s = pd.read_sql(
            "SELECT station_id, station_name, airviro_code "
            "FROM mart.dim_station ORDER BY station_name", conn)
        i = pd.read_sql(
            "SELECT indicator_id, indicator_name, formula, unit "
            "FROM mart.dim_indicator ORDER BY indicator_id", conn)
    return s, i


@st.cache_data(ttl=300)
def load_comparison(station_id: int, indicator_id: int) -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT ts_hour, measured_value, forecast_value, abs_error
            FROM mart.fact_air_quality_comparison
            WHERE station_id = %(s)s AND indicator_id = %(i)s
            ORDER BY ts_hour
            """,
            conn, params={"s": station_id, "i": indicator_id})
    if not df.empty:
        df["ts_eesti"] = df["ts_hour"].dt.tz_convert("Europe/Tallinn")
    return df


@st.cache_data(ttl=60)
def load_quality_tests() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql(
            """
            SELECT DISTINCT ON (test_name)
                test_name, status, rows_checked, rows_failing, details
            FROM quality.test_results
            ORDER BY test_name, run_at DESC
            """, conn)


stations, indicators = load_dims()
if stations.empty or indicators.empty:
    st.error("Andmebaasis pole dimensioone. Käivita scripts/seed_dimensions.py.")
    st.stop()

stations["label"] = stations["station_name"] + " (" + stations["airviro_code"] + ")"
indicators["label"] = (indicators["indicator_name"] + " ("
                       + indicators["formula"].apply(clean_formula) + ")")

c1, c2 = st.columns(2)
with c1:
    st_label = st.selectbox("Jaam", stations["label"])
with c2:
    ind_label = st.selectbox("Saasteaine", indicators["label"])

station = stations[stations["label"] == st_label].iloc[0]
indicator = indicators[indicators["label"] == ind_label].iloc[0]

df = load_comparison(int(station["station_id"]), int(indicator["indicator_id"]))

if df.empty:
    st.warning("Selle jaama ja saasteaine kohta võrdlusandmeid pole.")
    st.stop()

mae = df["abs_error"].mean()
max_err = df["abs_error"].max()
corr = df[["measured_value", "forecast_value"]].corr().iloc[0, 1]
unit = indicator["unit"]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Tunde võrreldud", f"{len(df)}")
k2.metric("MAE", f"{mae:.2f} {unit}")
k3.metric("Suurim viga", f"{max_err:.2f} {unit}")
k4.metric("Korrelatsioon", f"{corr:.3f}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df["ts_eesti"], y=df["measured_value"],
                         name="Mõõdetud", line=dict(color="#1f77b4", width=2)))
fig.add_trace(go.Scatter(x=df["ts_eesti"], y=df["forecast_value"],
                         name="CAMS prognoos",
                         line=dict(color="#ff7f0e", width=2, dash="dot")))
fig.update_layout(
    title=f"{station['station_name']} — {indicator['indicator_name']}",
    xaxis_title="Aeg (Eesti aeg)",
    yaxis_title=f"{clean_formula(indicator['formula'])} ({unit})",
    hovermode="x unified", height=500,
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Andmekvaliteedi testid (viimane käivitus)")
q = load_quality_tests()
if q.empty:
    st.info("Quality testid pole veel käivitatud.")
else:
    q["status"] = q["status"].map({"passed": "✓ passed", "failed": "✗ failed"})
    st.dataframe(q, use_container_width=True, hide_index=True)