"""
EstiMüük OÜ müügitõhususe pipeline — sünteetilised andmed → dbt

Töövoog:
    genereeri_andmed >> dbt_run >> dbt_test

    genereeri_andmed — kontrollib, kas staging tabel on tühi.
                       Kui jah, käivitab generate_data.py.
                       Kui ei, jätab genereerimise vahele.
    dbt_run          — käivitab kõik dbt mudelid (seed + run)
    dbt_test         — käivitab dbt schema testid

Ajakava: @daily — uued andmed genereeritakse igapäevaselt.
         Esimesel käivitusel genereeritakse 90 päeva ajalugu.
"""

import subprocess
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


def genereeri_andmed_kui_tühi(**context):
    """
    Genereerib sünteetilised andmed ainult siis, kui staging tabel on tühi.
    See tagab idempotentsuse — käivitused ei kahekordista andmeid.
    """
    hook = PostgresHook(postgres_conn_id="analytics_db")
    arv = hook.get_first("SELECT COUNT(*) FROM staging.raw_myygiandmed")[0]

    if arv > 0:
        print(f"Staging tabelis on juba {arv} rida. Genereerimine vahele jäetud.")
        return

    print("Staging tabel on tühi. Alustan sünteetiliste andmete genereerimisega...")
    result = subprocess.run(
        [sys.executable, "/opt/airflow/scripts/generate_data.py"],
        capture_output=True,
        text=True,
        env={
            **__import__("os").environ,
            "DB_HOST": "analytics-db",
            "DB_PORT": "5432",
            "DB_USER": __import__("os").environ.get("POSTGRES_USER", "praktikum"),
            "DB_PASSWORD": __import__("os").environ.get("POSTGRES_PASSWORD", "praktikum"),
            "DB_NAME": __import__("os").environ.get("POSTGRES_DB", "praktikum"),
        },
    )
    print(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"Generaator ebaõnnestus:\n{result.stderr}")


with DAG(
    dag_id="myyk_pipeline",
    description="Genereerib EstiMüük OÜ sünteetilised andmed ja käivitab dbt",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["synteetilised-andmed", "naidisprojekt"],
) as dag:

    genereeri = PythonOperator(
        task_id="genereeri_andmed",
        python_callable=genereeri_andmed_kui_tühi,
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

    genereeri >> dbt_run >> dbt_test
