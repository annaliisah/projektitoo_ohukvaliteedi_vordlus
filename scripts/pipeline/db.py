"""Andmebaasi ühenduse helper + pipeline_runs audit."""
import json
import os
from contextlib import contextmanager
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _conninfo() -> str:
    return (
        f"host={os.environ.get('DB_HOST', 'localhost')} "
        f"port={os.environ.get('DB_PORT_HOST', '55432')} "
        f"dbname={os.environ['POSTGRES_DB']} "
        f"user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )


@contextmanager
def get_conn():
    """Lihtne ühendus auto-commit/rollback'iga."""
    conn = psycopg.connect(_conninfo())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def pipeline_run(source: str, params: dict | None = None):
    """Logib jooksu staging.pipeline_runs-i. Yield-ib (conn, run_id, set_rows).

    Kasutus:
        with pipeline_run("ohuseire_monitoring", {...}) as (conn, run_id, set_rows):
            ...
            set_rows(n)
    """
    conn = psycopg.connect(_conninfo())
    rows = {"n": 0}

    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO staging.pipeline_runs (source, params) "
                "VALUES (%s, %s::jsonb) RETURNING run_id",
                [source, json.dumps(params or {})],
            )
            run_id = cur.fetchone()[0]
        conn.commit()

        yield conn, run_id, lambda n: rows.update(n=n)

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE staging.pipeline_runs "
                "SET finished_at = now(), status = 'success', rows_loaded = %s "
                "WHERE run_id = %s",
                [rows["n"], run_id],
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE staging.pipeline_runs "
                "SET finished_at = now(), status = 'failed', error_message = %s "
                "WHERE run_id = %s",
                [str(e)[:500], run_id],
            )
        conn.commit()
        raise
    finally:
        conn.close()