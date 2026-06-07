-- Transform staging -> mart.fact_air_quality_observation
-- Idempotentne: ON CONFLICT DO UPDATE värskema source_run_id-ga.
--
-- Andmete korrastamine:
--   measured: väikesed negatiivsed väärtused (-0.5..0) on mõõteinstrumendi
--   nullpunkti müra; clip-ime 0-ks. Suuremad negatiivsed jäävad alles ja
--   quality test annab nendest teada.

-- 1) Mõõdetud (ohuseire) -> 'measured'
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

-- 2) Prognoositud (Open-Meteo) -> 'forecast'
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

    
-- 3) Õhukvaliteedi indeks per saasteaine + üldine indeks per (jaam, tund, observation_type)
-- Allikas: Eesti Õhuaruanne 2022 tabel (NO2, PM10, O3, PM2.5)
-- Skaala: 1 = väga hea, 5 = väga halb. SO2-le indeksit ei arvuta (tabelis lävesid pole).
-- Üldindeks = halvim (kõrgeim) üksiku saasteaine indeks samal tunnil samas jaamas.
CREATE OR REPLACE VIEW mart.fact_air_quality_index AS
WITH per_pollutant AS (
    SELECT
        o.station_id,
        o.ts_hour,
        o.observation_type,
        o.indicator_id,
        o.value,
        CASE
            -- NO2 (ohuseire indicator_id = 3)
            WHEN o.indicator_id = 3 THEN
                CASE
                    WHEN o.value IS NULL THEN NULL
                    WHEN o.value <  50  THEN 1
                    WHEN o.value < 100  THEN 2
                    WHEN o.value < 200  THEN 3
                    WHEN o.value < 400  THEN 4
                    ELSE 5
                END
            -- PM10 (indicator_id = 21)
            WHEN o.indicator_id = 21 THEN
                CASE
                    WHEN o.value IS NULL THEN NULL
                    WHEN o.value <  25  THEN 1
                    WHEN o.value <  50  THEN 2
                    WHEN o.value <  90  THEN 3
                    WHEN o.value < 180  THEN 4
                    ELSE 5
                END
            -- O3 (indicator_id = 6)
            WHEN o.indicator_id = 6 THEN
                CASE
                    WHEN o.value IS NULL THEN NULL
                    WHEN o.value <  60  THEN 1
                    WHEN o.value < 120  THEN 2
                    WHEN o.value < 180  THEN 3
                    WHEN o.value < 240  THEN 4
                    ELSE 5
                END
            -- PM2.5 (indicator_id = 23)
            WHEN o.indicator_id = 23 THEN
                CASE
                    WHEN o.value IS NULL THEN NULL
                    WHEN o.value <  15  THEN 1
                    WHEN o.value <  30  THEN 2
                    WHEN o.value <  55  THEN 3
                    WHEN o.value < 110  THEN 4
                    ELSE 5
                END
            -- SO2 ja muud: indeksit ei arvuta
            ELSE NULL
        END AS pollutant_index
    FROM mart.fact_air_quality_observation o
)
SELECT
    station_id,
    ts_hour,
    observation_type,
    MAX(pollutant_index) AS overall_index
FROM per_pollutant
WHERE pollutant_index IS NOT NULL
GROUP BY station_id, ts_hour, observation_type;