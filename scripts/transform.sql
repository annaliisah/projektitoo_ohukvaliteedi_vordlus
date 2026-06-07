-- Transform staging -> mart kihi tabelid ja vaated.
-- Idempotentne: ON CONFLICT DO UPDATE.

-- ============================================================
-- 1) FACT: Mõõdetud (ohuseire) -> 'measured'
-- ============================================================
INSERT INTO mart.fact_air_quality_observation
    (station_id, indicator_id, ts_hour, observation_type, value, source_run_id)
SELECT
    m.station_id,
    m.indicator_id,
    date_trunc('hour', m.measured_at) AS ts_hour,
    'measured' AS observation_type,
    CASE
        WHEN m.value IS NULL THEN NULL
        WHEN m.value < 0 AND m.value >= -0.5 THEN 0
        ELSE m.value
    END AS value,
    m.run_id AS source_run_id
FROM staging.ohuseire_monitoring_raw m
WHERE m.run_id = (
    SELECT max(run_id) FROM staging.pipeline_runs
    WHERE source = 'ohuseire_monitoring' AND status = 'success'
)
ON CONFLICT (station_id, indicator_id, ts_hour, observation_type)
DO UPDATE SET
    value = EXCLUDED.value,
    source_run_id = EXCLUDED.source_run_id;

-- ============================================================
-- 2) FACT: Prognoositud (Open-Meteo) -> 'forecast'
-- ============================================================
INSERT INTO mart.fact_air_quality_observation
    (station_id, indicator_id, ts_hour, observation_type, value, source_run_id)
SELECT
    o.station_id,
    d.indicator_id,
    date_trunc('hour', o.forecast_at) AS ts_hour,
    'forecast' AS observation_type,
    o.value,
    o.run_id AS source_run_id
FROM staging.openmeteo_airquality_raw o
JOIN mart.dim_indicator d ON d.openmeteo_code = o.indicator_code
WHERE o.run_id = (
    SELECT max(run_id) FROM staging.pipeline_runs
    WHERE source = 'openmeteo_airquality' AND status = 'success'
)
ON CONFLICT (station_id, indicator_id, ts_hour, observation_type)
DO UPDATE SET
    value = EXCLUDED.value,
    source_run_id = EXCLUDED.source_run_id;


-- ============================================================
-- 3) VIEW: pollutant_index — üksiku saasteaine indeks 1-6
-- ============================================================
-- Allikas: Euroopa Keskkonnaagentuur (EEA) European Air Quality Index
--          https://airindex.eea.europa.eu/Map/AQI/Viewer/
-- Skaala: 1 = Hea ... 6 = Eriti halb.
CREATE OR REPLACE VIEW mart.fact_pollutant_index AS
SELECT
    o.station_id,
    o.indicator_id,
    o.ts_hour,
    o.observation_type,
    o.value,
    CASE
        -- SO2 (indicator_id = 1)
        WHEN o.indicator_id = 1 THEN
            CASE WHEN o.value IS NULL THEN NULL
                 WHEN o.value <  20  THEN 1
                 WHEN o.value <  40  THEN 2
                 WHEN o.value < 125  THEN 3
                 WHEN o.value < 190  THEN 4
                 WHEN o.value < 275  THEN 5
                 ELSE 6 END
        -- NO2 (indicator_id = 3)
        WHEN o.indicator_id = 3 THEN
            CASE WHEN o.value IS NULL THEN NULL
                 WHEN o.value <  10  THEN 1
                 WHEN o.value <  25  THEN 2
                 WHEN o.value <  60  THEN 3
                 WHEN o.value < 100  THEN 4
                 WHEN o.value < 150  THEN 5
                 ELSE 6 END
        -- O3 (indicator_id = 6)
        WHEN o.indicator_id = 6 THEN
            CASE WHEN o.value IS NULL THEN NULL
                 WHEN o.value <  60  THEN 1
                 WHEN o.value < 100  THEN 2
                 WHEN o.value < 120  THEN 3
                 WHEN o.value < 160  THEN 4
                 WHEN o.value < 180  THEN 5
                 ELSE 6 END
        -- PM10 (indicator_id = 21)
        WHEN o.indicator_id = 21 THEN
            CASE WHEN o.value IS NULL THEN NULL
                 WHEN o.value <  15  THEN 1
                 WHEN o.value <  45  THEN 2
                 WHEN o.value < 120  THEN 3
                 WHEN o.value < 195  THEN 4
                 WHEN o.value < 270  THEN 5
                 ELSE 6 END
        -- PM2.5 (indicator_id = 23)
        WHEN o.indicator_id = 23 THEN
            CASE WHEN o.value IS NULL THEN NULL
                 WHEN o.value <   5  THEN 1
                 WHEN o.value <  15  THEN 2
                 WHEN o.value <  50  THEN 3
                 WHEN o.value <  90  THEN 4
                 WHEN o.value < 140  THEN 5
                 ELSE 6 END
        ELSE NULL
    END AS pollutant_index
FROM mart.fact_air_quality_observation o;


-- ============================================================
-- 4) VIEW: air_quality_index — üldindeks per (jaam, tund, obs_type)
-- ============================================================
-- Üldindeks = halvim (kõrgeim) üksiku saasteaine indeks samal tunnil samas jaamas.
CREATE OR REPLACE VIEW mart.fact_air_quality_index AS
SELECT
    station_id,
    ts_hour,
    observation_type,
    MAX(pollutant_index) AS overall_index
FROM mart.fact_pollutant_index
WHERE pollutant_index IS NOT NULL
GROUP BY station_id, ts_hour, observation_type;


-- ============================================================
-- 5) VIEW: metrics — MAE, bias, korrelatsioon per (jaam, saasteaine)
-- ============================================================
CREATE OR REPLACE VIEW mart.fact_air_quality_metrics AS
SELECT
    station_id,
    indicator_id,
    COUNT(*) AS n_observations,
    AVG(abs_error) AS mae,
    AVG(forecast_value - measured_value) AS bias,
    CORR(forecast_value, measured_value) AS correlation
FROM mart.fact_air_quality_comparison
WHERE measured_value IS NOT NULL AND forecast_value IS NOT NULL
GROUP BY station_id, indicator_id;


-- ============================================================
-- 6) VIEW: hourly_error — tunni-põhine keskmine viga
-- ============================================================
-- Iga (jaam, saasteaine, tund 0-23) kohta keskmine prognoosi viga.
-- Tund arvutatud Eesti aja järgi, et oleks intuitiivne.
CREATE OR REPLACE VIEW mart.fact_hourly_error AS
SELECT
    station_id,
    indicator_id,
    EXTRACT(HOUR FROM ts_hour AT TIME ZONE 'Europe/Tallinn')::int AS hour_local,
    AVG(forecast_value - measured_value) AS avg_error,
    COUNT(*) AS n
FROM mart.fact_air_quality_comparison
WHERE measured_value IS NOT NULL AND forecast_value IS NOT NULL
GROUP BY station_id, indicator_id, hour_local;


-- ============================================================
-- 7) VIEW: index_match — kas measured ja forecast indeks klapivad
-- ============================================================
CREATE OR REPLACE VIEW mart.fact_index_match AS
SELECT
    m.station_id,
    m.ts_hour,
    m.overall_index AS measured_index,
    f.overall_index AS forecast_index,
    (m.overall_index = f.overall_index) AS levels_match
FROM mart.fact_air_quality_index m
JOIN mart.fact_air_quality_index f
    ON  m.station_id = f.station_id
    AND m.ts_hour    = f.ts_hour
WHERE m.observation_type = 'measured'
  AND f.observation_type = 'forecast';