"""Täida mart.dim_station ja mart.dim_indicator ohuseire API metaandmetest."""
import os

import requests

from scripts.pipeline.db import get_conn

# Ohuseire indicator_id -> Open-Meteo air quality muutuja nimi
OPENMETEO_CODES = {
    1: "sulphur_dioxide",   # SO2
    3: "nitrogen_dioxide",  # NO2
    6: "ozone",             # O3
    21: "pm10",             # PM10
    23: "pm2_5",            # PM2.5
}


def seed_stations(codes: list[str]) -> None:
    features = requests.get(
        "https://www.ohuseire.ee/api/station/et",
        params={"type": "INDICATOR"}, timeout=30,
    ).json()["features"]

    rows = [
        (
            f["id"],
            f["properties"]["name"],
            f["properties"]["airviro_code"],
            f["properties"]["type"],
            f["geometry"]["coordinates"][1],  # lat
            f["geometry"]["coordinates"][0],  # lon
        )
        for f in features
        if f["properties"]["airviro_code"] in codes
    ]

    with get_conn() as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO mart.dim_station
                (station_id, station_name, airviro_code, station_type, lat, lon)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (station_id) DO UPDATE SET
                station_name = EXCLUDED.station_name,
                airviro_code = EXCLUDED.airviro_code,
                station_type = EXCLUDED.station_type,
                lat = EXCLUDED.lat,
                lon = EXCLUDED.lon,
                updated_at = now()
            """,
            rows,
        )
    print(f"dim_station: {len(rows)} rida")


def seed_indicators(ids: list[int]) -> None:
    items = requests.get(
        "https://www.ohuseire.ee/api/indicator/et",
        params={"type": "INDICATOR"}, timeout=30,
    ).json()

    rows = [
        (
            i["id"],
            i["name"],
            i["formula"],
            i["unit"],
            OPENMETEO_CODES[i["id"]],
            i.get("description"),
        )
        for i in items
        if i["id"] in ids
    ]

    with get_conn() as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO mart.dim_indicator
                (indicator_id, indicator_name, formula, unit,
                 openmeteo_code, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (indicator_id) DO UPDATE SET
                indicator_name = EXCLUDED.indicator_name,
                formula = EXCLUDED.formula,
                unit = EXCLUDED.unit,
                openmeteo_code = EXCLUDED.openmeteo_code,
                description = EXCLUDED.description,
                updated_at = now()
            """,
            rows,
        )
    print(f"dim_indicator: {len(rows)} rida")


def main():
    stations = os.environ["STATIONS"].split(",")
    indicator_ids = [int(x) for x in os.environ["INDICATOR_IDS"].split(",")]
    seed_stations(stations)
    seed_indicators(indicator_ids)


if __name__ == "__main__":
    main()