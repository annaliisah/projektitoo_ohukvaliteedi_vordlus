# Edenemisraport

## Mis on valmis

- Docker Compose käivitab kõik teenused: analytics-db, Airflow, Superset.
- `generate_data.py` genereerib 90 päeva sünteetilisi müügiandmeid 8 kaupluse kohta.
- Airflow DAG kontrollib, kas andmed on olemas, ja genereerib vajaduse korral.
- dbt seed laadib `pood.csv` → `marts.pood` tabelisse.
- dbt staging mudel (`stg_myygiandmed`) puhastab toorandmed.
- dbt intermediate mudel (`int_myyk_tunnipohine`) arvutab müügitõhususe.
- dbt marts mudelid (`mart_pood_paevane`, `mart_parimad_tunnid`) on töös.
- dbt testid läbivad.
- Superset on käivitunud aadressil http://localhost:8088 (admin/admin).

## Järgmised sammud

- Luua Superset'is andmebaasi ühendus analytics-db'ga.
- Ehitada 3 chart'i: kaupluste paremusjärjestus, kellaajamustrite joondiagramm, KPI paarik.
- Eksportida dashboard ZIP-failina → commitida reposse.
- Täpsustada README piirangute ja järelduste osa (sünteetiliste andmete hoiatused).

## Mis takistab

- Superset'i esimene käivitamine võtab ~3 minutit — oota, enne kui proovid sisse logida.
- Kui port 8088 on hõivatud (kasutatakse juba ilmaandmete projektis), muuda `.env` failis `SUPERSET_PORT_HOST` väärtust (nt `8089`).

## Kontrollpunkt

```bash
# Kontrolli, et kõik teenused töötavad
docker compose ps

# Kontrolli andmete olemasolu
docker compose exec analytics-db psql -U praktikum -c \
  "SELECT pood_id, COUNT(*) FROM staging.raw_myygiandmed GROUP BY 1 ORDER BY 1"

# Käivita DAG käsitsi esimesel korral (kui @daily veel ei ole käivitanud)
# Ava Airflow UI: http://localhost:8080 → myyk_pipeline → Trigger DAG
```

Oodatav tulemus: 8 kauplust, igaühel ~1000–1500 rida (90 päeva × ~12–14 avatud tundi).
