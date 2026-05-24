"""
Ilmaandmete pipeline — Open-Meteo → staging → dbt run → dbt test

Lihtne järjestikune DAG (ilma TaskFlow API ja dynamic task mapping'uta):
    laadi_ilmaandmed >> dbt_run >> dbt_test

Ajakava: iga tund (@hourly), catchup=False — vahele jäänud käivitusi ei korduta.
"""

import ssl
import uuid
from datetime import datetime, timezone

import requests
import urllib3
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from requests.adapters import HTTPAdapter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class _LaxHTTPSAdapter(HTTPAdapter):
    """Ajutine lahendus Python 3.12 + OpenSSL 3.x + Docker MTU probleemile.

    HOIATUS: See lülitab TLS sertifikaadi kontrollimise välja ja ei ole sobiv
    produktsioonikeskkonda. Avaliku ilmaAPI puhul õppekeskkonnas aktsepteeritav,
    kuna andmed ei ole tundlikud. Pärisrakenduses kasuta urllib3>=2.0 või httpx.
    """

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0)
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


def _session() -> requests.Session:
    s = requests.Session()
    s.mount("https://", _LaxHTTPSAdapter())
    return s

# Asukohtade nimekiri — koordinaadid vastavad seeds/asukohad.csv failile
ASUKOHAD = [
    {"id": "tallinn",     "nimi": "Tallinn",     "lat": 59.4370, "lon": 24.7536},
    {"id": "tartu",       "nimi": "Tartu",       "lat": 58.3776, "lon": 26.7290},
    {"id": "parnu",       "nimi": "Pärnu",       "lat": 58.3858, "lon": 24.5046},
    {"id": "narva",       "nimi": "Narva",       "lat": 59.3772, "lon": 28.1903},
    {"id": "rakvere",     "nimi": "Rakvere",     "lat": 59.3470, "lon": 26.3576},
    {"id": "viljandi",    "nimi": "Viljandi",    "lat": 58.3636, "lon": 25.5958},
    {"id": "kuressaare",  "nimi": "Kuressaare",  "lat": 58.2479, "lon": 22.5052},
    {"id": "haapsalu",    "nimi": "Haapsalu",    "lat": 58.9442, "lon": 23.5439},
    {"id": "voru",        "nimi": "Võru",        "lat": 57.8333, "lon": 27.0167},
    {"id": "jogeva",      "nimi": "Jõgeva",      "lat": 58.7453, "lon": 26.3953},
]

API_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_DAYS = 7


def laadi_ilmaandmed(**context):
    """
    Küsib Open-Meteo API-st prognoosi kõigi asukohtade kohta ja laadib
    tulemused staging.ilmaandmed_raw tabelisse.
    """
    hook = PostgresHook(postgres_conn_id="analytics_db")
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Loo pipeline_runs kirje olekuga 'running'
    hook.run(
        """
        INSERT INTO staging.pipeline_runs
            (run_id, fetched_at, source_name, forecast_days, status)
        VALUES (%s, %s, 'open-meteo', %s, 'running')
        """,
        parameters=(run_id, now, FORECAST_DAYS),
    )

    try:
        for asukoht in ASUKOHAD:
            resp = _session().get(
                API_URL,
                params={
                    "latitude":        asukoht["lat"],
                    "longitude":       asukoht["lon"],
                    "hourly": (
                        "temperature_2m,"
                        "precipitation,"
                        "precipitation_probability,"
                        "wind_speed_10m,"
                        "is_day"
                    ),
                    "wind_speed_unit": "ms",
                    "timezone":        "Europe/Tallinn",
                    "forecast_days":   FORECAST_DAYS,
                },
                timeout=30,
            )
            resp.raise_for_status()
            tunniandmed = resp.json()["hourly"]
            allikas_url = resp.url

            read = [
                (
                    run_id,
                    asukoht["id"],
                    asukoht["nimi"],
                    asukoht["lat"],
                    asukoht["lon"],
                    tunniandmed["time"][i],
                    tunniandmed["temperature_2m"][i],
                    tunniandmed["precipitation"][i],
                    tunniandmed["precipitation_probability"][i],
                    tunniandmed["wind_speed_10m"][i],
                    tunniandmed["is_day"][i],
                    now,
                    allikas_url,
                )
                for i in range(len(tunniandmed["time"]))
            ]

            hook.insert_rows(
                table="staging.ilmaandmed_raw",
                rows=read,
                target_fields=[
                    "run_id", "asukoha_id", "asukoha_nimi",
                    "laiuskraad", "pikkuskraad", "prognoos_aeg",
                    "temperatuur_c", "sademed_mm", "sademe_toenaosus_pct",
                    "tuulekiirus_ms", "on_paev",
                    "laetud_kell", "allikas_url",
                ],
            )

        # Märgi käivitus õnnestunuks
        hook.run(
            "UPDATE staging.pipeline_runs SET status = 'success' WHERE run_id = %s",
            parameters=(run_id,),
        )

    except Exception as exc:
        hook.run(
            """
            UPDATE staging.pipeline_runs
            SET status = 'failed', message = %s
            WHERE run_id = %s
            """,
            parameters=(str(exc), run_id),
        )
        raise


with DAG(
    dag_id="ilmaandmed_pipeline",
    description="Laeb Open-Meteo prognoosi ja käivitab dbt transformatsioonid",
    schedule="@hourly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["ilmaandmed", "naidisprojekt"],
) as dag:

    lae_andmed = PythonOperator(
        task_id="laadi_ilmaandmed",
        python_callable=laadi_ilmaandmed,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt seed --profiles-dir . && "
            "dbt run --profiles-dir ."
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt test --profiles-dir ."
        ),
    )

    lae_andmed >> dbt_run >> dbt_test
