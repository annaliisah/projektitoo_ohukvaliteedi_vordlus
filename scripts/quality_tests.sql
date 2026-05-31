-- Andmekvaliteedi testid -> quality.test_results
-- Iga test on üks INSERT, mis logib oma tulemuse.

-- Test 1: fact_no_negative_values
INSERT INTO quality.test_results
    (test_name, status, rows_checked, rows_failing, details)
SELECT
    'fact_no_negative_values',
    CASE WHEN COUNT(*) FILTER (WHERE value < 0) = 0
         THEN 'passed' ELSE 'failed' END,
    COUNT(*),
    COUNT(*) FILTER (WHERE value < 0),
    'Mõõdetud ja prognoositud väärtused peavad olema >= 0'
FROM mart.fact_air_quality_observation
WHERE value IS NOT NULL;

-- Test 2: fact_pk_unique
INSERT INTO quality.test_results
    (test_name, status, rows_checked, rows_failing, details)
WITH dup AS (
    SELECT station_id, indicator_id, ts_hour, observation_type, COUNT(*) c
    FROM mart.fact_air_quality_observation
    GROUP BY 1, 2, 3, 4
    HAVING COUNT(*) > 1
)
SELECT
    'fact_pk_unique',
    CASE WHEN (SELECT COUNT(*) FROM dup) = 0
         THEN 'passed' ELSE 'failed' END,
    (SELECT COUNT(*) FROM mart.fact_air_quality_observation),
    (SELECT COALESCE(SUM(c), 0) FROM dup),
    'Loogiline PK: (station_id, indicator_id, ts_hour, observation_type)';

-- Test 3: fact_indicators_have_dim
INSERT INTO quality.test_results
    (test_name, status, rows_checked, rows_failing, details)
SELECT
    'fact_indicators_have_dim',
    CASE WHEN COUNT(*) FILTER (WHERE d.indicator_id IS NULL) = 0
         THEN 'passed' ELSE 'failed' END,
    COUNT(*),
    COUNT(*) FILTER (WHERE d.indicator_id IS NULL),
    'Iga fact-rea indicator_id peab eksisteerima dim_indicator-is'
FROM mart.fact_air_quality_observation f
LEFT JOIN mart.dim_indicator d ON d.indicator_id = f.indicator_id;

-- Test 4: fact_measurements_recent
INSERT INTO quality.test_results
    (test_name, status, rows_checked, rows_failing, details)
WITH latest AS (
    SELECT MAX(ts_hour) AS ts
    FROM mart.fact_air_quality_observation
    WHERE observation_type = 'measured'
)
SELECT
    'fact_measurements_recent',
    CASE WHEN (SELECT ts FROM latest) >= now() - INTERVAL '6 hours'
         THEN 'passed' ELSE 'failed' END,
    1,
    CASE WHEN (SELECT ts FROM latest) >= now() - INTERVAL '6 hours'
         THEN 0 ELSE 1 END,
    'Viimane mõõtmine peab olema <= 6 tundi vana. Viimane: '
        || COALESCE((SELECT ts::text FROM latest), 'puudub');