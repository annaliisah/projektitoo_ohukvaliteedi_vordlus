"""Streamlit dashboard: mõõdetud vs Open-Meteo CAMS prognoos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from scripts.pipeline.db import get_conn

# EEA European Air Quality Index — 6 tase värvid ja sildid.
INDEX_COLORS = ["#50f0e6", "#50ccaa", "#f0e641", "#ff5050", "#960032", "#7d2181"]
INDEX_LABELS = ["Hea", "Rahuldav", "Keskmine", "Halb", "Väga halb", "Eriti halb"]

# Saasteained, millele on indeks olemas (vastab SQL CASE WHEN-i listile).
INDEXED_INDICATORS = {1, 3, 6, 21, 23}


st.set_page_config(page_title="Õhukvaliteedi võrdlus", layout="wide")

st.markdown("""
<style>
[data-testid="metric-container"] {
    background-color: white;
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
[data-baseweb="select"] {
    background-color: gray;
    border-radius: 10px;
}
[data-testid="stMetric"] {
    background-color: gray;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
[data-testid="stDataFrame"] {
    background-color: gray;
    border-radius: 12px;
    padding: 10px;
}
h1 { color: #1f3b6f; }
</style>
""", unsafe_allow_html=True)

st.title("Õhukvaliteet: mõõdetud vs CAMS prognoos")
st.caption(
    "Võrdlus Eesti õhuseire mõõteandmete ja Open-Meteo CAMS mudelprognoosi vahel."
)


def clean_formula(s: str) -> str:
    return s.replace("<sub>", "").replace("</sub>", "")


# Andmete laadimine — kõik mart kihist, ainult SELECT-id.

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
def load_pollutant_data(station_id: int, indicator_id: int) -> pd.DataFrame:
    """Mõõdetud + prognoos + viga + pollutant_index — kõik samal real."""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT
                c.ts_hour,
                c.measured_value,
                c.forecast_value,
                c.diff AS error,
                c.abs_error,
                m_idx.pollutant_index AS measured_index,
                f_idx.pollutant_index AS forecast_index
            FROM mart.fact_air_quality_comparison c
            LEFT JOIN mart.fact_pollutant_index m_idx
                ON  m_idx.station_id   = c.station_id
                AND m_idx.indicator_id = c.indicator_id
                AND m_idx.ts_hour      = c.ts_hour
                AND m_idx.observation_type = 'measured'
            LEFT JOIN mart.fact_pollutant_index f_idx
                ON  f_idx.station_id   = c.station_id
                AND f_idx.indicator_id = c.indicator_id
                AND f_idx.ts_hour      = c.ts_hour
                AND f_idx.observation_type = 'forecast'
            WHERE c.station_id = %(s)s AND c.indicator_id = %(i)s
            ORDER BY c.ts_hour
            """,
            conn, params={"s": station_id, "i": indicator_id})
    if not df.empty:
        df["ts_eesti"] = df["ts_hour"].dt.tz_convert("Europe/Tallinn")
    return df


@st.cache_data(ttl=300)
def load_metrics(station_id: int, indicator_id: int) -> dict:
    """Eelarvutatud MAE, bias, korrelatsioon."""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT n_observations, mae, bias, correlation
            FROM mart.fact_air_quality_metrics
            WHERE station_id = %(s)s AND indicator_id = %(i)s
            """,
            conn, params={"s": station_id, "i": indicator_id})
    if df.empty:
        return {}
    row = df.iloc[0]
    return {"n": int(row["n_observations"]), "mae": row["mae"],
            "bias": row["bias"], "corr": row["correlation"]}


@st.cache_data(ttl=300)
def load_hourly_error(station_id: int, indicator_id: int) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql(
            """
            SELECT hour_local AS hour, avg_error
            FROM mart.fact_hourly_error
            WHERE station_id = %(s)s AND indicator_id = %(i)s
            ORDER BY hour_local
            """,
            conn, params={"s": station_id, "i": indicator_id})


@st.cache_data(ttl=300)
def load_index_timeseries(station_id: int) -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT ts_hour, observation_type, overall_index
            FROM mart.fact_air_quality_index
            WHERE station_id = %(s)s
            ORDER BY ts_hour
            """,
            conn, params={"s": station_id})
    if not df.empty:
        df["ts_eesti"] = df["ts_hour"].dt.tz_convert("Europe/Tallinn")
    return df


@st.cache_data(ttl=300)
def load_index_match(station_id: int) -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT ts_hour, measured_index, forecast_index, levels_match
            FROM mart.fact_index_match
            WHERE station_id = %(s)s
            ORDER BY ts_hour
            """,
            conn, params={"s": station_id})
    if not df.empty:
        df["ts_eesti"] = df["ts_hour"].dt.tz_convert("Europe/Tallinn")
    return df


@st.cache_data(ttl=300)
def load_thresholds(indicator_id: int) -> pd.DataFrame:
    """Loeme indeksi läved otse SQL-st (per saasteaine), et need oleksid
    ühes kohas. Tuletame ülempiir = MIN(value) sees, kus pollutant_index
    on järgmise taseme oma."""
    with get_conn() as conn:
        df = pd.read_sql(
            """
            SELECT pollutant_index AS level,
                   MIN(value) AS lower_bound,
                   MAX(value) AS upper_bound
            FROM mart.fact_pollutant_index
            WHERE indicator_id = %(i)s
              AND pollutant_index IS NOT NULL
              AND value IS NOT NULL
            GROUP BY pollutant_index
            ORDER BY pollutant_index
            """,
            conn, params={"i": indicator_id})
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


# Abifunktsioonid graafikute jaoks (puhas visuaal).

def value_to_color(value, df_observed: pd.DataFrame, indicator_id: int) -> str:
    """Tagasta värv väärtusele, kasutades pollutant_index andmeid samal real."""
    return "#888888"  # asendatakse all real-data lookup'iga


def add_colored_line(fig, df, y_col: str, index_col: str, name: str, dash: str = "solid"):
    """Värvilised segmendid — värv tuleb SQL pollutant_index veerust."""
    x = df["ts_eesti"].tolist()
    y = df[y_col].tolist()
    idx = df[index_col].tolist()
    for i in range(len(x) - 1):
        if y[i] is None or y[i+1] is None or pd.isna(y[i]) or pd.isna(y[i+1]):
            continue
        # Värv = kõrgema otsa taseme värv (kui väärtus läbib lävi, näeme kohe)
        level_left = idx[i] if not pd.isna(idx[i]) else None
        level_right = idx[i+1] if not pd.isna(idx[i+1]) else None
        if level_left is None and level_right is None:
            color = "#888888"
        else:
            level = max(level_left or 1, level_right or 1)
            color = INDEX_COLORS[int(level) - 1]
        fig.add_trace(go.Scatter(
            x=[x[i], x[i+1]],
            y=[y[i], y[i+1]],
            mode="lines",
            line=dict(color=color, width=2.5, dash=dash),
            showlegend=False,
            hoverinfo="skip",
        ))
    # Legendi näiv trace
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="lines",
        line=dict(color="#888888", width=2.5, dash=dash),
        name=name,
    ))


def add_threshold_lines(fig, thresholds_df: pd.DataFrame, x_min, x_max):
    """Horisontaalsed katkendlikud abijooned indeksi tasemete piiridel."""
    # Tase N ülempiir = (N+1) taseme alumine piir
    sorted_df = thresholds_df.sort_values("level")
    for i in range(len(sorted_df) - 1):
        current_level = int(sorted_df.iloc[i]["level"])
        # Tase 6-l (Eriti halb) pole ülempiiri
        if current_level >= 6:
            continue
        # Ülempiir = järgmise taseme alumine väärtus selles datas
        # (Lihtsam: võtame järgmise taseme min)
        upper = sorted_df.iloc[i + 1]["lower_bound"]
        if upper is None or pd.isna(upper):
            continue
        fig.add_shape(
            type="line", xref="x", yref="y",
            x0=x_min, x1=x_max, y0=upper, y1=upper,
            line=dict(color="rgba(180,180,180,0.4)", width=1, dash="dash"),
            layer="below",
        )
        fig.add_annotation(
            x=x_max, y=upper, xref="x", yref="y",
            text=f"{INDEX_LABELS[current_level - 1]}",
            showarrow=False,
            xanchor="left", yanchor="middle",
            font=dict(size=9, color="rgba(180,180,180,0.7)"),
        )



# UI


stations, indicators = load_dims()
if stations.empty or indicators.empty:
    st.error("Andmebaasis pole dimensioone. Käivita scripts/seed_dimensions.py. "
             "Kui skript on juba käivitatud, värskenda lehte 30 sekundi pärast")
    st.stop()

stations["label"] = stations["station_name"] + " (" + stations["airviro_code"] + ")"
indicators["label"] = (indicators["indicator_name"] + " ("
                       + indicators["formula"].apply(clean_formula) + ")")

c1, c2, c3 = st.columns(3)

with c1:
    st_label = st.selectbox("Jaam", stations["label"])
with c2:
    ind_label = st.selectbox("Saasteaine", indicators["label"])

station = stations[stations["label"] == st_label].iloc[0]
indicator = indicators[indicators["label"] == ind_label].iloc[0]
ind_id = int(indicator["indicator_id"])
station_id = int(station["station_id"])
unit = indicator["unit"]
has_index = ind_id in INDEXED_INDICATORS

# Andmed (kõik vajalik korraga)
df = load_pollutant_data(station_id, ind_id)
if df.empty:
    st.warning("Selle jaama ja saasteaine kohta võrdlusandmeid pole.")
    st.stop()

st.caption(f"{len(df)} vaatlust")

with c3:
    date_range = st.date_input(
        "Periood",
        value=(df["ts_eesti"].min().date(), df["ts_eesti"].max().date())
    )

if len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df["ts_eesti"].dt.date >= start_date)
            & (df["ts_eesti"].dt.date <= end_date)]

if df.empty:
    st.warning("Valitud perioodis võrdlusandmeid pole.")
    st.stop()

# Mõõdikud
metrics = load_metrics(station_id, ind_id)

k1, k2, k3 = st.columns(3)
with k1:
    st.metric("MAE", f"{metrics['mae']:.2f} {unit}" if metrics else "–")
with k2:
    st.metric("Korrelatsioon", f"{metrics['corr']:.3f}" if metrics else "–")
with k3:
    st.metric("Keskmine nihe", f"{metrics['bias']:.2f} {unit}" if metrics else "–")

# Tõlgenduskastid
j1, j2 = st.columns(2)
if metrics:
    with j1:
        corr = metrics["corr"]
        if corr is None:
            st.info("**Prognoosi täpsus:** korrelatsiooni ei saa arvutada.")
        elif corr > 0.8:
            st.success("**Prognoosi täpsus:** Väga hea")
        elif corr > 0.5:
            st.warning("**Prognoosi täpsus:** Keskmine")
        else:
            st.error("**Prognoosi täpsus:** Nõrk")
    with j2:
        bias = metrics["bias"]
        if abs(bias) < 0.5:
            st.success("**Süstemaatiline nihe:** ei ole märgata.")
        elif bias > 0:
            st.warning("**Süstemaatiline nihe:** CAMS kipub üle hindama.")
        else:
            st.warning("**Süstemaatiline nihe:** CAMS kipub alahindama.")

st.divider()
st.subheader("Joonised")

fig = go.Figure()
if has_index:
    th_df = load_thresholds(ind_id)
    if not th_df.empty:
        add_threshold_lines(fig, th_df,
                            df["ts_eesti"].min(), df["ts_eesti"].max())
    add_colored_line(fig, df, "measured_value", "measured_index",
                     "Mõõdetud väärtus", dash="solid")
    add_colored_line(fig, df, "forecast_value", "forecast_index",
                     "CAMS prognoos", dash="dot")
else:
    fig.add_trace(go.Scatter(x=df["ts_eesti"], y=df["measured_value"],
                             name="Mõõdetud väärtus",
                             line=dict(color="#1f77b4", width=2)))
    fig.add_trace(go.Scatter(x=df["ts_eesti"], y=df["forecast_value"],
                             name="CAMS prognoos",
                             line=dict(color="#ff7f0e", width=2, dash="dot")))
fig.update_layout(
    title=f"{indicator['indicator_name']} kontsentratsioon {station['station_name']} mõõtejaamas",
    xaxis_title="Kuupäev",
    yaxis_title=f"{clean_formula(indicator['formula'])} ({unit})",
    hovermode="x unified", height=500,
)
st.plotly_chart(fig, use_container_width=True)

# Vea graafik
err_fig = go.Figure()
err_fig.add_trace(go.Scatter(
    x=df["ts_eesti"], y=df["error"],
    name="Prognoosiviga",
    line=dict(color="#d62728", width=2)
))
err_fig.update_layout(
    title=f"{indicator['indicator_name']} prognoosi kõrvalekalle mõõdetud väärtustest",
    xaxis_title="Kuupäev", yaxis_title=f"Viga ({unit})",
    hovermode="x unified", height=350,
    yaxis=dict(zeroline=True,
               zerolinecolor="rgba(125,125,125,0.8)", zerolinewidth=1),
)
st.plotly_chart(err_fig, use_container_width=True)

# Tunnipõhine viga
hourly_df = load_hourly_error(station_id, ind_id)
hour_fig = go.Figure()
hour_fig.add_trace(go.Bar(
    x=hourly_df["hour"], y=hourly_df["avg_error"],
    name="Keskmine prognoosiviga"
))
hour_fig.update_layout(
    title="Kas prognoos eksib rohkem teatud kellaaegadel?",
    xaxis_title="Tund (Eesti aeg)", yaxis_title=f"Keskmine viga ({unit})",
    height=400,
    yaxis=dict(zeroline=True,
               zerolinecolor="rgba(125,125,125,0.8)", zerolinewidth=1),
)
st.plotly_chart(hour_fig, use_container_width=True)


# Õhukvaliteedi indeks (üldine, sõltumatu valitud saasteainest)
st.divider()
st.subheader("Õhukvaliteedi indeks")
st.caption(
    "Üldindeks per tund = halvim üksiku saasteaine indeks "
    "(EEA European Air Quality Index, 6 taset: 1=Hea ... 6=Eriti halb)."
)

idx_df = load_index_timeseries(station_id)
match_df = load_index_match(station_id)

if len(date_range) == 2:
    idx_df = idx_df[(idx_df["ts_eesti"].dt.date >= date_range[0])
                    & (idx_df["ts_eesti"].dt.date <= date_range[1])]
    match_df = match_df[(match_df["ts_eesti"].dt.date >= date_range[0])
                        & (match_df["ts_eesti"].dt.date <= date_range[1])]

if idx_df.empty:
    st.info("Selle jaama ja perioodi kohta indeksi andmeid pole.")
else:
    idx_measured = idx_df[idx_df["observation_type"] == "measured"]
    idx_forecast = idx_df[idx_df["observation_type"] == "forecast"]

    idx_fig = go.Figure()
    # Värvilised horisontaalribad indeksi tasemete jaoks
    for level in range(1, 7):
        idx_fig.add_shape(
            type="rect", xref="paper", yref="y",
            x0=0, x1=1, y0=level - 0.5, y1=level + 0.5,
            fillcolor=INDEX_COLORS[level - 1], opacity=0.15,
            layer="below", line=dict(width=0),
        )
    idx_fig.add_trace(go.Scatter(
        x=idx_measured["ts_eesti"], y=idx_measured["overall_index"],
        name="Mõõdetud indeks",
        line=dict(color="#1f77b4", width=2),
        mode="lines+markers", marker=dict(size=6),
    ))
    idx_fig.add_trace(go.Scatter(
        x=idx_forecast["ts_eesti"], y=idx_forecast["overall_index"],
        name="Prognoositud indeks",
        line=dict(color="#ff7f0e", width=2, dash="dot"),
        mode="lines+markers", marker=dict(size=6),
    ))
    idx_fig.update_layout(
        title=f"Üldindeks {station['station_name']} jaamas",
        xaxis_title="Kuupäev",
        yaxis=dict(
            title="Indeks",
            tickmode="array",
            tickvals=[1, 2, 3, 4, 5, 6],
            ticktext=[f"{i} {INDEX_LABELS[i-1]}" for i in range(1, 7)],
            range=[0.5, 6.5],
        ),
        hovermode="x unified", height=450,
    )
    st.plotly_chart(idx_fig, use_container_width=True)

    # KPI-d indeksi võrdluseks — kõik eelarvutatud mart-st
    latest_m = idx_measured["overall_index"].iloc[-1] if not idx_measured.empty else None
    avg_m = idx_measured["overall_index"].mean() if not idx_measured.empty else None
    match_pct = (100 * match_df["levels_match"].sum() / len(match_df)
                 if len(match_df) > 0 else None)

    i1, i2, i3 = st.columns(3)
    with i1:
        if latest_m is not None:
            lvl = int(latest_m)
            st.metric("Viimane mõõdetud indeks", f"{lvl} {INDEX_LABELS[lvl-1]}")
        else:
            st.metric("Viimane mõõdetud indeks", "–")
    with i2:
        st.metric("Perioodi keskmine (mõõdetud)",
                  f"{avg_m:.2f}" if avg_m is not None else "–")
    with i3:
        st.metric("Indeks klapib prognoosiga",
                  f"{match_pct:.0f} %" if match_pct is not None else "–")


# Andmekvaliteedi testid

st.divider()
st.subheader("Andmekvaliteedi testid (viimane käivitus)")
q = load_quality_tests()
if q.empty:
    st.info("Andmekvaliteedi testid pole veel käivitatud.")
else:
    q["status"] = q["status"].map({"passed": "✓ läbitud", "failed": "✗ ei ole läbitud"})
    st.dataframe(q, use_container_width=True, hide_index=True)

failed_tests = (q["status"] == "failed").sum() if not q.empty else 0
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