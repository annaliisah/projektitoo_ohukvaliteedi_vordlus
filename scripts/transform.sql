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