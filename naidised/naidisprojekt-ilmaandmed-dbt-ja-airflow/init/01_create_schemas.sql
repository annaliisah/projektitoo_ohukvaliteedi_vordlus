-- Loob skeemid ja toorandmete tabelid.
-- dbt loob oma mudelid (staging vaated, intermediate vaated, marts tabelid) ise,
-- kuid raw staging tabelid peab enne looma, et Airflow saaks neisse kirjutada.

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;

-- Töövoo käivituste jälgimine
CREATE TABLE IF NOT EXISTS staging.pipeline_runs (
    run_id       uuid        PRIMARY KEY,
    fetched_at   timestamptz NOT NULL,
    source_name  text        NOT NULL,
    forecast_days integer    NOT NULL,
    status       text        NOT NULL,  -- 'running' | 'success' | 'failed'
    message      text
);

-- Toorandmed Open-Meteo API-st (üks rida = üks asukoht × üks prognoositund)
CREATE TABLE IF NOT EXISTS staging.ilmaandmed_raw (
    run_id                   uuid         NOT NULL REFERENCES staging.pipeline_runs(run_id),
    asukoha_id               text         NOT NULL,
    asukoha_nimi             text         NOT NULL,
    laiuskraad               numeric(9,4) NOT NULL,
    pikkuskraad              numeric(9,4) NOT NULL,
    prognoos_aeg             timestamp    NOT NULL,
    temperatuur_c            numeric(6,2),
    sademed_mm               numeric(8,2),
    sademe_toenaosus_pct     integer,
    tuulekiirus_ms           numeric(8,2),
    on_paev                  integer,          -- 0 = öö, 1 = päev
    laetud_kell              timestamptz  NOT NULL,
    allikas_url              text         NOT NULL,
    PRIMARY KEY (run_id, asukoha_id, prognoos_aeg)
);
