"""Tõmba Open-Meteo CAMS prognoosid valitud jaamadele stagingusse."""
import json
import os
from datetime import datetime, timedelta

import requests

from scripts.pipeline.db import get_conn, pipeline_run

URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

INSERT_SQL = """
    INSERT INTO staging.openmeteo_airquality_raw
        (run_id, station_id, indicator_code, forecast_at, value, raw)
    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
    ON CONFLICT DO NOTHING
"""


def fetch(lat: float, lon: float, codes: list[str],
          start: datetime, end: datetime) -> dict:
    r = requests.get(URL, timeout=60, params={
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(codes),
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "timezone": "UTC",
        "domains": "cams_europe",
    })
    r.raise_for_status()
    return r.json()


def main():
    days = int(os.environ.get("LOAD_DAYS", "7"))
    end = datetime.now()
    start = end - timedelta(days=days)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT station_id, lat, lon FROM mart.dim_station "
            "WHERE airviro_code = ANY(%s)",
            [os.environ["STATIONS"].split(",")],
        )
        stations = cur.fetchall()  # [(id, lat, lon), ...]

        cur.execute(
            "SELECT openmeteo_code FROM mart.dim_indicator "
            "WHERE indicator_id = ANY(%s) ORDER BY indicator_id",
            [[int(x) for x in os.environ["INDICATOR_IDS"].split(",")]],
        )
        codes = [r[0] for r in cur.fetchall()]

    print(f"Periood: {start:%Y-%m-%d} – {end:%Y-%m-%d} ({days} päeva)")
    print(f"Jaamad: {[s[0] for s in stations]}, koodid: {codes}")

    params = {"days": days,
              "stations": [s[0] for s in stations],
              "codes": codes}

    with pipeline_run("openmeteo_airquality", params) as (conn, run_id, set_rows):
        total = 0
        with conn.cursor() as cur:
            for sid, lat, lon in stations:
                data = fetch(lat, lon, codes, start, end)
                times = data["hourly"]["time"]
                rows = []
                for code in codes:
                    values = data["hourly"][code]
                    for t, v in zip(times, values):
                        rows.append((
                            run_id, sid, code, t, v,
                            json.dumps({"time": t, "value": v, "code": code}),
                        ))
                if rows:
                    cur.executemany(INSERT_SQL, rows)
                print(f"  jaam {sid} ({lat}, {lon}): {len(rows)} rida")
                total += len(rows)

        set_rows(total)
        print(f"Kokku: {total} rida (run_id={run_id})")


if __name__ == "__main__":
    main()