"""Tõmba ohuseire mõõtmised viimase LOAD_DAYS päeva kohta staging-sse.

Ohuseire API tagastab measured-välja Eesti kohalikus ajas (Europe/Tallinn)
ilma timezone-i infota. Konverteerime UTC-sse enne salvestamist."""
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from scripts.pipeline.db import get_conn, pipeline_run

URL = "https://www.ohuseire.ee/api/monitoring/et"
TALLINN = ZoneInfo("Europe/Tallinn")
UTC = ZoneInfo("UTC")

INSERT_SQL = """
    INSERT INTO staging.ohuseire_monitoring_raw
        (run_id, station_id, indicator_id, measured_at, value, raw)
    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
    ON CONFLICT DO NOTHING
"""


def parse_measured(s: str) -> datetime:
    """'2026-05-31 15:00:00' (Eesti aeg) -> UTC datetime."""
    naive = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    return naive.replace(tzinfo=TALLINN).astimezone(UTC)


def fetch(station_id: int, indicator_id: int,
          start: datetime, end: datetime) -> list[dict]:
    r = requests.get(URL, timeout=60, params={
        "type": "INDICATOR",
        "stations": str(station_id),
        "indicators": str(indicator_id),
        "range": f"{start:%d.%m.%Y},{end:%d.%m.%Y}",
    })
    r.raise_for_status()
    return r.json()


def main():
    days = int(os.environ.get("LOAD_DAYS", "7"))
    end = datetime.now(TALLINN)
    start = end - timedelta(days=days)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT station_id FROM mart.dim_station "
            "WHERE airviro_code = ANY(%s)",
            [os.environ["STATIONS"].split(",")],
        )
        station_ids = [r[0] for r in cur.fetchall()]

    indicator_ids = [int(x) for x in os.environ["INDICATOR_IDS"].split(",")]

    print(f"Periood: {start:%d.%m.%Y} – {end:%d.%m.%Y} ({days} päeva)")
    print(f"Jaamad: {station_ids}, indikaatorid: {indicator_ids}")

    params = {"days": days, "stations": station_ids,
              "indicators": indicator_ids}

    with pipeline_run("ohuseire_monitoring", params) as (conn, run_id, set_rows):
        total = 0
        with conn.cursor() as cur:
            for sid in station_ids:
                for iid in indicator_ids:
                    items = fetch(sid, iid, start, end)
                    rows = [
                        (run_id, sid, iid,
                         parse_measured(item["measured"]),
                         item.get("value"), json.dumps(item))
                        for item in items
                    ]
                    if rows:
                        cur.executemany(INSERT_SQL, rows)
                    print(f"  jaam {sid}, indikaator {iid}: {len(rows)} rida")
                    total += len(rows)

        set_rows(total)
        print(f"Kokku: {total} rida (run_id={run_id})")


if __name__ == "__main__":
    main()