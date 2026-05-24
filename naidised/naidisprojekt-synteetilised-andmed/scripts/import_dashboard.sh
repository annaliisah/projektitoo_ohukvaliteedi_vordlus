#!/usr/bin/env bash
# Impordib Superset dashboard'i definitsioonid repost.
#
# Kasutamine:
#   1. Käivita projekt: docker compose up -d
#   2. Oota, kuni Superset on käivitunud (http://localhost:8088)
#   3. Käivita see skript: bash scripts/import_dashboard.sh

set -e

DASHBOARD_FILE="superset/dashboards/myyk_dashboard.zip"
CONTAINER="synteetilised-superset"

if [ ! -f "$DASHBOARD_FILE" ]; then
  echo "Dashboard faili '$DASHBOARD_FILE' ei leitud."
  echo "Superset dashboard eksportimiseks:"
  echo "  1. Ava Superset: http://localhost:8088 (admin/admin)"
  echo "  2. Loo ühendus analytics-db andmebaasiga:"
  echo "     Settings > Database Connections > + Database"
  echo "     SQLAlchemy URI: postgresql+psycopg2://praktikum:praktikum@analytics-db:5432/praktikum"
  echo "  3. Loo chart'id ja dashboard"
  echo "  4. Ekspordi: Dashboards > ... > Export"
  echo "  5. Salvesta ZIP fail siia: $DASHBOARD_FILE"
  exit 1
fi

echo "Kopeerime dashboard faili konteinerisse..."
docker compose cp "$DASHBOARD_FILE" "$CONTAINER:/app/dashboards/dashboard.zip"

echo "Impordime dashboard'i Supersetti..."
docker compose exec "$CONTAINER" superset import-dashboards \
  --path /app/dashboards/dashboard.zip \
  --username admin

echo "Valmis! Ava Superset: http://localhost:8088"
