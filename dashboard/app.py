"""Streamlit dashboard: mõõdetud vs Open-Meteo CAMS prognoos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from scripts.pipeline.db import get_conn

st.set_page_config(page_title="Õhukvaliteedi võrdlus", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #f3f8ff;
}

[data-testid="metric-container"] {
    background-color: white;
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

[data-baseweb="select"] {
    background-color: white;
    border-radius: 10px;
}

[data-testid="stMetric"] {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
           
[data-testid="stDataFrame"] {
    background-color: white;
    border-radius: 12px;
    padding: 10px;
}

h1 {
    color: #1f3b6f;
}
</style>
""", unsafe_allow_html=True)


st.title("Õhukvaliteet: mõõdetud vs CAMS prognoos")
st.caption(
    "Võrdlus Eesti õhuseire mõõteandmete ja Open-Meteo CAMS mudelprognoosi vahel."
)


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


st.markdown('<div class="kpi-card">', unsafe_allow_html=True)                                              

c1, c2, c3 = st.columns(3)

with c1:
    st_label = st.selectbox("Jaam", stations["label"])

with c2:
    ind_label = st.selectbox("Saasteaine", indicators["label"])

station = stations[stations["label"] == st_label].iloc[0]
indicator = indicators[indicators["label"] == ind_label].iloc[0]

df = load_comparison(
    int(station["station_id"]),
    int(indicator["indicator_id"])
)

if df.empty:
    st.warning("Selle jaama ja saasteaine kohta võrdlusandmeid pole.")
    st.stop()

st.caption(
    f"{len(df)} vaatlust" 
)

with c3:
    date_range = st.date_input(
        "Periood",
        value=(
            df["ts_eesti"].min().date(),
            df["ts_eesti"].max().date()
        )
    )

st.markdown("</div>", unsafe_allow_html=True)

if len(date_range) == 2:
    start_date, end_date = date_range
    df = df[
        (df["ts_eesti"].dt.date >= start_date)
        & (df["ts_eesti"].dt.date <= end_date)
    ]

if df.empty:
    st.warning("Valitud perioodis võrdlusandmeid pole.")
    st.stop()

df["error"] = df["forecast_value"] - df["measured_value"]

mae = df["abs_error"].mean()
max_err = df["abs_error"].max()
corr = df[["measured_value", "forecast_value"]].corr().iloc[0, 1]
bias = df["error"].mean()


unit = indicator["unit"]

k1, k2, k3 = st.columns(3)

with k1:
    st.metric("MAE", f"{mae:.2f} {unit}")

with k2:
    st.metric("Korrelatsioon", f"{corr:.3f}")

with k3:
    st.metric("Keskmine nihe", f"{bias:.2f} {unit}")

st.markdown('</div>', unsafe_allow_html=True)

j1, j2 = st.columns(2)

with j1:
    if corr > 0.8:
        st.success("**Prognoosi täpsus:** Väga hea")
    elif corr > 0.5:
        st.warning("**Prognoosi täpsus:** Keskmine")
    else:
        st.error("**Prognoosi täpsus:** Nõrk")

with j2:
    if abs(bias) < 0.5:
        st.success("**Süstemaatiline nihe:** ei ole märgata.")
    elif bias > 0:
        st.warning("**Süstemaatiline nihe:** CAMS kipub üle hindama.")
    else:
        st.warning("**Süstemaatiline nihe:** CAMS kipub alahindama.")

st.divider()
st.subheader("Joonised")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df["ts_eesti"], y=df["measured_value"],
                         name="Mõõdetud väärtus", line=dict(color="#1f77b4", width=2)))
fig.add_trace(go.Scatter(x=df["ts_eesti"], y=df["forecast_value"],
                         name="CAMS prognoos",
                         line=dict(color="#ff7f0e", width=2, dash="dot")))
fig.update_layout(
    title=f"{indicator['indicator_name']} kontsentratsioon {station['station_name']} mõõtejaamas",
    xaxis_title="Kuupäev",
    yaxis_title=f"{clean_formula(indicator['formula'])} ({unit})",
    hovermode="x unified", height=500,
)

st.plotly_chart(fig, use_container_width=True, key="main_time_chart")

err_fig = go.Figure()

err_fig.add_trace(go.Scatter(
    x=df["ts_eesti"],
    y=df["error"],
    name="Prognoosiviga",
    line=dict(color="#d62728", width=2)
))

err_fig.add_trace(go.Scatter(
    x=[df["ts_eesti"].min(), df["ts_eesti"].max()],
    y=[0, 0],
    mode="lines",
    name="Täpse prognoosi tase (viga = 0)",
    line=dict(color="black", dash="dash")
))

err_fig.update_layout(
title=f"{indicator['indicator_name']} prognoosi kõrvalekalle mõõdetud väärtustest",
    xaxis_title="Kuupäev",
    yaxis_title=f"Viga ({unit})",
    hovermode="x unified",
    height=350,
)

st.plotly_chart(err_fig, use_container_width=True)


hourly_error = df.copy()
hourly_error["hour"] = hourly_error["ts_eesti"].dt.hour

hourly_summary = (
    hourly_error
    .groupby("hour", as_index=False)["error"]
    .mean()
)

hour_fig = go.Figure()

hour_fig.add_trace(go.Bar(
    x=hourly_summary["hour"],
    y=hourly_summary["error"],
    name="Keskmine prognoosiviga"
))

hour_fig.add_trace(go.Scatter(
    x=[hourly_summary["hour"].min(), hourly_summary["hour"].max()],
    y=[0, 0],
    mode="lines",
    name="Viga = 0",
    line=dict(dash="dash")
))

hour_fig.update_layout(
    title="Kas prognoos eksib rohkem teatud kellaaegadel?",
    xaxis_title="Tund",
    yaxis_title=f"Keskmine viga ({unit})",
    height=400
)

st.plotly_chart(hour_fig, use_container_width=True)

st.subheader("Andmekvaliteedi testid (viimane käivitus)")
q = load_quality_tests()
if q.empty:
    st.info("Andmekvaliteedi testid pole veel käivitatud.")
else:
    q["status"] = q["status"].map({"passed": "✓ läbitud", "failed": "✗ ei ole läbitud"})
    st.dataframe(q, use_container_width=True, hide_index=True)

failed_tests = (q["status"] == "failed").sum()

if failed_tests == 0:
    st.success(
        "Kõik andmekvaliteedi kontrollid läbisid edukalt. "
        "Andmed on värsked, unikaalsed ning vastavad etteantud reeglitele."
    )
else:
    st.error(
        f"Andmekvaliteedi kontrollides tuvastati {failed_tests} probleem(i). "
        "Vaata ülalolevat tabelit täpsemaks infoks."
    )