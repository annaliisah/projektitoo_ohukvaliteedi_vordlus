#!/usr/bin/env bash
# Impordib Superset dashboard'i definitsioonid repost.
#
# Kasutamine:
#   1. Käivita projekt: docker compose up -d
#   2. Oota, kuni Superset on käivitunud (http://localhost:8088)
#   3. Käivita see skript: bash scripts/import_dashboard.sh
#
# Dashboard eksport asub: superset/dashboards/ilmaandmed_dashboard.zip
# (lisatakse reposse pärast projekti esmakordset seadistamist)

set -e

DASHBOARD_FILE="superset/dashboards/ilmaandmed_dashboard.zip"
CONTAINER="ilmaandmed-superset"

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
  echo "  6. Commiti ZIP fail reposse"
  exit 1
fi

echo "Kopeerime dashboard faili konteinerisse..."
docker compose cp "$DASHBOARD_FILE" "$CONTAINER:/tmp/dashboard.zip"

echo "Impordime dashboard'i Supersetti..."
docker compose exec "$CONTAINER" superset import-dashboards \
  --path /tmp/dashboard.zip \
  --username admin

echo "Valmis! Ava Superset: http://localhost:8088"
