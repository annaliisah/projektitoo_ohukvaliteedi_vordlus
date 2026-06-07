#!/bin/bash
# Käivitab kogu pipeline'i järjest. Kasutatakse nii esmakÃ¤ivitusel kui ka cron scheduleris iga tund.
set -e

echo "==> [$(date -u +%Y-%m-%dT%H:%M:%SZ)] Pipeline algab"

echo "==> Seed dimensions"
python -m scripts.seed_dimensions

echo "==> Fetch ohuseire monitoring"
python -m scripts.fetch_ohuseire_monitoring

echo "==> Fetch Open-Meteo airquality"
python -m scripts.fetch_openmeteo_airquality

echo "==> Transform"
PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$DB_HOST" -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -f scripts/transform.sql

echo "==> Quality tests"
PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$DB_HOST" -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -f scripts/quality_tests.sql

echo "==> [$(date -u +%Y-%m-%dT%H:%M:%SZ)] Pipeline lõpetatud"
