import requests
import psycopg2
import os

import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Andmebaasi ühenduse seaded (loetakse keskkonnamuutujatest)
## originaal näitest ei töötanud
# DB_CONFIG = {
#     "host": os.getenv("DB_HOST", "db"),
#     "port": int(os.getenv("DB_PORT", 5432)),
#     "dbname": os.environ["POSTGRES_DB"],
#     "user": os.environ["POSTGRES_USER"],
#     "password": os.environ["POSTGRES_PASSWORD"],
# }

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.environ.get("POSTGRES_DB"),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
}

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
params = {
	"latitude": 59.41,
	"longitude": 24.65,
	"hourly": ["pm10", "pm2_5", "ozone", "nitrogen_dioxide", "sulphur_dioxide"],
	"past_days": 31,
	"domains": "cams_europe",
    "timezone": "GMT", ## TODO: mis timezone kasutame
}


### - kõik andmed openmeteost tulevad mikrogrammi per m3
def extract():

    responses = openmeteo.weather_api(API_URL, params = params)
    response = responses[0]
    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_pm10 = hourly.Variables(0).ValuesAsNumpy()
    hourly_pm2_5 = hourly.Variables(1).ValuesAsNumpy()
    hourly_ozone = hourly.Variables(2).ValuesAsNumpy()
    hourly_nitrogen_dioxide = hourly.Variables(3).ValuesAsNumpy()
    hourly_sulphur_dioxide = hourly.Variables(4).ValuesAsNumpy()
    
    hourly_data = {
        "date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )
    }

    hourly_data["pm10"] = hourly_pm10
    hourly_data["pm2_5"] = hourly_pm2_5
    hourly_data["ozone"] = hourly_ozone
    hourly_data["nitrogen_dioxide"] = hourly_nitrogen_dioxide
    hourly_data["sulphur_dioxide"] = hourly_sulphur_dioxide
    hourly_data["coordinate_lat"] = params["latitude"]
    hourly_data["coordinate_lon"] = params["longitude"]
    hourly_data["ohuseire_jaam"] = "oismae"

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    
    return hourly_dataframe


def transform(raw_data):
    """
    Transform: puhasta ja normaliseeri andmed.

    Sisend: JSON list API-st (iga element on dict)
    Väljund: list tuple'itest kujul (name, capital, population, area, continent)
    """
    # käi raw_data üle, võta igast elemendist vajalikud väljad, tagasta list tuple'itest
    tulemus = []

    # print("raw data type on: ", type(raw_data))
    # print("len raw data on: ", len(raw_data))
    # print("raw data: ", raw_data.head(100))
    for index, row in raw_data.iterrows():
        kuupaev = row["date"]
        pm10 = row["pm10"]
        pm2_5 = row["pm2_5"]
        ozone = row["ozone"]
        nitrogen_dioxide = row["nitrogen_dioxide"]
        sulphur_dioxide = row["sulphur_dioxide"]
        coordinates = (row["coordinate_lat"], row["coordinate_lon"])
        ohuseire_jaam = row["ohuseire_jaam"]
        ## TODO: leida SO2 piirid indeksi leidmiseks
        if nitrogen_dioxide > 400 or pm10 > 180 or pm2_5 > 110 or ozone > 240:
            indeksi_vaartus = "vaga korge"
        elif nitrogen_dioxide > 200 or pm10 > 90 or pm2_5 > 55 or ozone > 180:
            indeksi_vaartus = "korge"
        elif nitrogen_dioxide > 100 or pm10 > 50 or pm2_5 > 30 or ozone > 120:
            indeksi_vaartus = "keskmine"
        elif nitrogen_dioxide > 50 or pm10 > 25 or pm2_5 > 15 or ozone > 60:
            indeksi_vaartus = "madal"
        elif nitrogen_dioxide >= 0 or pm10 >= 0 or pm2_5 >= 0 or ozone >= 0:
            indeksi_vaartus = "vaga madal"
        else:
            indeksi_vaartus = "puudub info"
        tulemus.append((kuupaev, ohuseire_jaam, coordinates, pm10, pm2_5, ozone, nitrogen_dioxide, sulphur_dioxide, indeksi_vaartus))

        # tulemus.append((name, capital, population, area, "Europe"))
    # tulemus.sort(key=lambda r: r[2], reverse=True)
    return tulemus



def load(rows):
    """
    Load: kirjuta andmed PostgreSQL tabelisse 

    Tabel peab sisaldama: id, name, capital, population, area_km2, continent, loaded_at
    Laadimine peab olema idempotentne (TRUNCATE enne laadimist).

    Näide kuidas PostgreSQL-iga ühenduda ja andmeid sisestada:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS test (id SERIAL PRIMARY KEY, name TEXT)")
        cur.execute("INSERT INTO test (name) VALUES (%s)", ("väärtus",))
        conn.commit()
        cur.close()
        conn.close()
    """

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    # cur.execute("DROP TABLE IF EXISTS openmeteo_andmed")
    cur.execute("CREATE TABLE IF NOT EXISTS openmeteo_andmed (id SERIAL PRIMARY KEY, date_gmt0 TIMESTAMP, ohuseire_jaam TEXT, coordinates TEXT, pm10 FLOAT, pm2_5 FLOAT, ozone FLOAT, nitrogen_dioxide FLOAT, sulphur_dioxide FLOAT, air_quality_index TEXT)")
    cur.execute("TRUNCATE TABLE openmeteo_andmed ")
    for row in rows:
        cur.execute("INSERT INTO openmeteo_andmed (date_gmt0, ohuseire_jaam, coordinates, pm10, pm2_5, ozone, nitrogen_dioxide, sulphur_dioxide, air_quality_index) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", row)
    conn.commit()
    cur.close()
    conn.close()
    return 


def main():
    print("=== ETL protsess ===\n")

    # Extract
    raw = extract()
    #print(f"Extracted: {len(raw)} kirjet\n")

    # # Transform
    rows = transform(raw)
    print(f"Transformed: {len(rows)} rida\n")

    # # Load
    load(rows)

    print("\n=== ETL lõpetatud ===")



if __name__ == "__main__":
    main()
    
    