
#Loeb .env failist ühenduse parameetrid ja pakub context manageri ühenduse jaoks
from __future__ import annotations
import os
from contextlib import contextmanager
from pathlib import Path
import psycopg
from dotenv import load_dotenv

# Lae .env fail projekti juurkaustast
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_conninfo() -> str:
    #Ehita psycopg conninfo string .env muutujatest
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db = os.environ["POSTGRES_DB"]
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT_HOST", "55432")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


@contextmanager
def get_conn():
    conn = psycopg.connect(get_conninfo())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()