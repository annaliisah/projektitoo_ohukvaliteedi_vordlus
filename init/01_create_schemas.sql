-- init/01_create_schemas.sql
-- Käivitub automaatselt PostgreSQL konteinerit käivitades
-- Loob skeemid ja kõik tabelid arhitektuuri järgi.


-- Skeemid
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS quality;


-- STAGING: toorandmed allikast
-- Iga ETL-jooks saab oma run_id, et oleks võimalik jälgida ja debugida
CREATE TABLE IF NOT EXISTS staging.pipeline_runs (
    run_id          BIGSERIAL PRIMARY KEY,
    source          TEXT NOT NULL,            -- 'ohuseire' | 'openmeteo'
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'running',  -- running | success | failed
    rows_loaded     INTEGER,
    params          JSONB,
    error_message   TEXT
);

-- Ohuseire jaamade metainfo (uueneb harva)
CREATE TABLE IF NOT EXISTS staging.ohuseire_stations_raw (
    run_id          BIGINT NOT NULL REFERENCES staging.pipeline_runs(run_id),
    loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload         JSONB NOT NULL
);

-- Ohuseire indikaatorite metainfo (uueneb harva)
CREATE TABLE IF NOT EXISTS staging.ohuseire_indicators_raw (
    run_id          BIGINT NOT NULL REFERENCES staging.pipeline_runs(run_id),
    loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload         JSONB NOT NULL
);

-- Ohuseire mõõtmised — üks rida = üks (jaam, näitaja, tund) mõõtmine
CREATE TABLE IF NOT EXISTS staging.ohuseire_monitoring_raw (
    run_id          BIGINT NOT NULL REFERENCES staging.pipeline_runs(run_id),
    loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    station_id      INTEGER NOT NULL,
    indicator_id    INTEGER NOT NULL,
    measured_at     TIMESTAMPTZ NOT NULL,
    value           DOUBLE PRECISION,
    raw             JSONB,
    PRIMARY KEY (station_id, indicator_id, measured_at, run_id)
);

-- Open-Meteo Air Quality (CAMS) prognoosid — üks rida = üks (jaam, näitaja, tund)
CREATE TABLE IF NOT EXISTS staging.openmeteo_airquality_raw (
    run_id          BIGINT NOT NULL REFERENCES staging.pipeline_runs(run_id),
    loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    station_id      INTEGER NOT NULL,         -- ohuseire jaama id (koordinaatide kaudu seotud)
    indicator_code  TEXT NOT NULL,            -- pm2_5 | pm10 | nitrogen_dioxide | sulphur_dioxide | ozone
    forecast_at     TIMESTAMPTZ NOT NULL,
    value           DOUBLE PRECISION,
    raw             JSONB,
    PRIMARY KEY (station_id, indicator_code, forecast_at, run_id)
);

-- MART: dimensioonid (staatilised või harva muutuvad)
CREATE TABLE IF NOT EXISTS mart.dim_station (
    station_id      INTEGER PRIMARY KEY,
    station_name    TEXT NOT NULL,
    airviro_code    TEXT,
    station_type    TEXT,
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mart.dim_indicator (
    indicator_id        INTEGER PRIMARY KEY,        -- ohuseire id
    indicator_name      TEXT NOT NULL,              -- nt 'PM2.5'
    formula             TEXT,                       -- nt 'PM2.5'
    unit                TEXT,                       -- nt 'µg/m³'
    openmeteo_code      TEXT,                       -- nt 'pm2_5' (mapping CAMS-i)
    description         TEXT,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MART: faktitabel — mõõdetud JA prognoositud read koos

-- observation_type = 'measured' | 'forecast'
CREATE TABLE IF NOT EXISTS mart.fact_air_quality_observation (
    station_id          INTEGER NOT NULL REFERENCES mart.dim_station(station_id),
    indicator_id        INTEGER NOT NULL REFERENCES mart.dim_indicator(indicator_id),
    ts_hour             TIMESTAMPTZ NOT NULL,
    observation_type    TEXT NOT NULL CHECK (observation_type IN ('measured', 'forecast')),
    value               DOUBLE PRECISION,
    source_run_id       BIGINT,
    PRIMARY KEY (station_id, indicator_id, ts_hour, observation_type)
);

CREATE INDEX IF NOT EXISTS ix_fact_obs_ts
    ON mart.fact_air_quality_observation (ts_hour);


-- MART: võrdlusvaade (measured + forecast samal real)
CREATE OR REPLACE VIEW mart.fact_air_quality_comparison AS
SELECT
    m.station_id,
    m.indicator_id,
    m.ts_hour,
    m.value                                AS measured_value,
    f.value                                AS forecast_value,
    (f.value - m.value)                    AS diff,
    ABS(f.value - m.value)                 AS abs_error
FROM mart.fact_air_quality_observation m
JOIN mart.fact_air_quality_observation f
    ON  m.station_id   = f.station_id
    AND m.indicator_id = f.indicator_id
    AND m.ts_hour      = f.ts_hour
WHERE m.observation_type = 'measured'
  AND f.observation_type = 'forecast';


-- QUALITY: andmekvaliteedi testide tulemused
CREATE TABLE IF NOT EXISTS quality.test_results (
    test_id         BIGSERIAL PRIMARY KEY,
    run_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    test_name       TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('passed', 'failed')),
    rows_checked    BIGINT,
    rows_failing    BIGINT,
    details         TEXT
);