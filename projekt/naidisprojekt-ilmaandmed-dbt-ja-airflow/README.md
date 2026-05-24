# Näidisprojekt: Ilmaandmed — Airflow + dbt + Superset

See näidisprojekt lahendab sama äriküsimuse mis `naidisprojekt-ilmaandmed`, kuid kasutab
**edasijõudnute stacki**: Airflow orkestreerib töövoo, dbt teeb transformatsioonid, Superset näitab tulemusi.

> Lihtsamat varianti (Python + Streamlit + cron) vaata kaustast `../naidisprojekt-ilmaandmed`.

## Äriküsimus

Millistes Eesti asulates ja millistel järgmistel päevadel on ilm kõige sobivam välitegevuste, rattasõidu või õues toimuva ürituse planeerimiseks?

**Mõõdikud:**
1. Välitegevuse sobivuse skoor (0–100) iga tunni kohta
2. Parimad 3-tunnised ajaaknad (kesk_skoor ≥ 50) päeva ja asukoha lõikes
3. Päevane soovitus (Väga sobiv / Sobiv / Piiripealne / Ebasoodne)

## Andmestik

| Allikas | Tüüp | Ajas muutuv? | Roll |
|---------|------|--------------|------|
| Open-Meteo Forecast API | Avalik HTTP API, ilma võtmeta | Jah, prognoos uueneb iga tunni järel | Põhiandmevoog — tunnipõhised ilmaandmed |
| `seeds/asukohad.csv` | Staatiline dbt seed | Ei, muutub ainult projekti muutmisel | Asukohtade koordinaadid API päringuteks |

## Stack

| Komponent | Tööriist |
|-----------|---------|
| Orkestreerimine | Apache Airflow 3.x |
| Transformatsioon | dbt Core 1.10 |
| Andmehoidla | PostgreSQL (pgDuckDB) |
| Näidikulaud | Apache Superset 6.x |
| Andmeallikas | Open-Meteo API (tasuta, ilma võtmeta) |

## Andmevoog lühidalt

1. **Sissevõtt** — Airflow DAG kutsub iga tund Open-Meteo API-t 10 Eesti asukoha kohta ja laadib vastuse `staging.ilmaandmed_raw` tabelisse.
2. **Laadimine** — Airflow `PythonOperator` kirjutab read `staging` kihti upsert-loogikaga (ON CONFLICT DO NOTHING).
3. **Transformatsioon** — `dbt run` ehitab staging vaate → intermediate skoorivaate → marts kokkuvõttetabelid.
4. **Testimine** — `dbt test` kontrollib 7 andmekvaliteedi testi (not_null, accepted_values).
5. **Näidikulaud** — Superset loeb `marts.*` tabeleid ja näitab linnade paremusjärjestust, parimaid ajavahemikke ja KPI-d.

## Andmevoog

```
Open-Meteo API
    ↓ (Airflow PythonOperator, @hourly)
staging.ilmaandmed_raw           ← toorandmed
    ↓ (dbt staging view)
staging.stg_ilmaandmed           ← puhastatud
    ↓ (dbt intermediate view)
intermediate.int_ilmaandmed_skoor ← tunnipõhine skoor (0–100)
    ↓ (dbt marts tables)
marts.mart_paeva_kokkuvote       ← päevane kokkuvõte
marts.mart_parimad_ajavahemikud  ← parimad 3h aknad
    ↓
Superset dashboard
```

## Projekti struktuur

```
.
├── compose.yml                    ← kõik teenused
├── .env.example                   ← kopeeri .env-iks
├── .gitignore
├── Dockerfile.superset
├── airflow/
│   └── dags/
│       └── ilmaandmed_pipeline.py ← Airflow DAG (fetch → dbt run → dbt test)
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── seeds/
│   │   └── asukohad.csv           ← 10 Eesti linna koordinaatidega
│   ├── models/
│   │   ├── staging/               ← 1 mudel + testid (stg_ilmaandmed)
│   │   ├── intermediate/          ← 1 mudel + testid (int_ilmaandmed_skoor)
│   │   └── marts/                 ← 2 mudelit + testid
│   └── macros/
│       └── generate_schema_name.sql
├── init/
│   └── 01_create_schemas.sql      ← loob staging skeemi ja toorandmete tabelid
├── superset/
│   ├── superset_config.py
│   └── dashboards/                ← dashboard ZIP (lisatakse pärast seadistust)
├── scripts/
│   └── import_dashboard.sh
└── docs/
    ├── arhitektuur.md             ← nädal 1 väljund
    └── progress.md                ← nädal 2 väljund
```

## Käivitamine

```bash
# 1. Kopeeri keskkonnamuutujad
cp .env.example .env

# 2. Genereeri turvaline SECRET_KEY Superseti jaoks
#    Asenda .env failis SUPERSET_SECRET_KEY väärtus:
python -c "import secrets; print(secrets.token_hex(32))"

# 3. Käivita kõik teenused
docker compose up -d --build

# 4. Oota ~2–3 minutit, kuni kõik teenused on käivitunud
docker compose ps   # kõik peaksid olema "running" või "healthy"

# 5. Ava Airflow UI ja käivita DAG käsitsi esimesel korral
#    http://localhost:8080  (kasutaja/parool: vt .env AIRFLOW_USER/PASSWORD)
#    → ilmaandmed_pipeline → "Trigger DAG" nupp

# 6. Ava Superset
#    http://localhost:8088  (kasutaja/parool: vt .env SUPERSET_ADMIN_USER/PASSWORD)
```

## Saladused ja konfiguratsioon

Kõik paroolid ja võtmed on `.env` failis. Reposse läheb ainult `.env.example`. Päris `.env` on `.gitignore`-s.

| Muutuja | Tähendus |
|---------|----------|
| `POSTGRES_PASSWORD` | Analüütika andmebaasi parool |
| `AIRFLOW_USER` / `AIRFLOW_PASSWORD` | Airflow UI sisselogimine |
| `SUPERSET_SECRET_KEY` | Superset'i sessiooniküpsiste krüptovõti — **genereeri uus**, ära jäta vaikeväärtust |
| `SUPERSET_ADMIN_USER` / `SUPERSET_ADMIN_PASSWORD` | Superset'i admin-kasutaja |
| `SUPERSET_DB_PASSWORD` | Superset'i metaandmebaasi parool |

## Andmekvaliteedi testid

dbt testid käivituvad automaatselt iga DAG-käivituse lõpus (`dbt test`). Testide ebaõnnestumine märgib Airflow töövoo punaseks.

1. `staging.stg_ilmaandmed` — kriitilised veerud ei ole NULL (temperatuur, sademed, tuulekiirus, `on_paev`)
2. `staging.stg_ilmaandmed` — `on_paev` on 0 või 1 (vigaste API vastuste tuvastamine)
3. `intermediate.int_ilmaandmed_skoor` — `koguskoor` ei ole NULL
4. `intermediate.int_ilmaandmed_skoor` — `sobivuse_silt` on üks neljast lubatud väärtusest
5. `marts.mart_paeva_kokkuvote` — `kesk_skoor` ja `paeva_soovitus` ei ole NULL
6. `marts.mart_paeva_kokkuvote` — `paeva_soovitus` on lubatud väärtuste hulgas
7. `marts.mart_parimad_ajavahemikud` — `kesk_skoor` ja `soovitus` ei ole NULL

## dbt käsud (käsitsi käivitamiseks)

```bash
# Ava Airflow konteineri shell (dbt on sealt kättesaadav):
docker compose exec ilmaandmed-airflow-apiserver bash

# dbt projekti kaustas:
cd /opt/airflow/dbt_project

dbt seed --profiles-dir .        # laadib asukohad.csv
dbt run --profiles-dir .         # käivitab kõik mudelid
dbt test --profiles-dir .        # käivitab testid
dbt docs generate --profiles-dir .  # genereerib dokumentatsiooni
```

## Superset seadistus

Kui DAG on vähemalt korra edukalt läbi jooksnud:

### 1. Loo andmebaasi ühendus

**Settings → Database Connections → + Database → PostgreSQL**

| Väli | Väärtus |
|------|---------|
| HOST | `analytics-db` |
| PORT | `5432` |
| DATABASE NAME | `praktikum` |
| USERNAME | `praktikum` |
| PASSWORD | `praktikum` |

### 2. Registreeri datasetid

**Datasets → + Dataset** — vali ühendus, seejärel:
- `marts` → `mart_paeva_kokkuvote`
- `marts` → `mart_parimad_ajavahemikud`

### 3. Loo chart'id

**Charts → + Chart** → vali dataset → vali chart tüüp → seadista → **Create chart** → Save.

> Kui Superset lisab automaatselt ajafiltri (nt `prognoos_kuupaev (No filter)`), jäta see `No filter` olekusse — eemaldada ei saa, aga `No filter` tähendab, et kõik andmed on nähtaval.

**Chart 1 — Linnade paremusjärjestus**
- Tüüp: **Bar Chart**, dataset: `mart_paeva_kokkuvote`
- **X-axis**: `asukoha_nimi`
- **Metrics**: `kesk_skoor` (AVG)
- **X-Axis Sort By**: `AVG(kesk_skoor)` + lülita sisse **Sort Descending**

**Chart 2 — Parimad ajaaknad**
- Tüüp: **Table**, dataset: `mart_parimad_ajavahemikud`
- **Columns**: `asukoha_nimi`, `vahemiku_algus`, `kesk_skoor`, `soovitus`
- **Row limit**: 50

**Chart 3 — Päevane KPI**
- Tüüp: **Big Number**, dataset: `mart_paeva_kokkuvote`
- **Metric**: `max_skoor` (MAX)

### 4. Loo dashboard

**Dashboards → + Dashboard** → anna nimi → lohista chart'id paika → Publish.

### 5. Ekspordi dashboard (ZIP reposse)

```bash
docker compose exec superset bash -c "superset export-dashboards \
  -f /tmp/ilmaandmed_dashboard.zip"

docker compose cp superset:/tmp/ilmaandmed_dashboard.zip \
  superset/dashboards/ilmaandmed_dashboard.zip
```

### 6. Impordi dashboard (kui ZIP on juba reposis)

```bash
bash scripts/import_dashboard.sh
```

## Kokkuvõte, puudused ja võimalikud edasiarendused

**Mis töötab:**
- Pipeline töötab end-to-end: Airflow → staging → dbt → Superset
- dbt testid kontrollivad andmekvaliteeti automaatselt iga käivituse lõpus
- Airflow käivitab töövoo automaatselt iga tund (`@hourly`)

**Teadlikud piirangud:**
- Superset dashboard tuleb esimesel korral käsitsi seadistada (andmebaasi ühendus, datasetid, chart'id)
- Asukohtade nimekiri on defineeritud kahes kohas: DAG-is ja `seeds/asukohad.csv` — ideaalis peaks olema üks allikas
- `staging.ilmaandmed_raw` kasvab piiramatult — vanade käivituste andmeid ei kustutata

**Võimalikud edasiarendused:**
- Lisada rohkem Eesti linnu seemnesse
- Automatiseerida Superset'i datasettide ja chart'ide loomine skriptiga
- Lisada `staging.pipeline_runs` põhjal Airflow sensor, mis kontrollib eelmise käivituse edukust enne uue alustamist

## Arhitektuur ja täpsemad otsused

Vaata: [`docs/arhitektuur.md`](docs/arhitektuur.md)

## Mida see näide NÄITAB vs mida EI NÄITA

**Näitab:**
- Airflow + dbt + Superset integreerimist ühes `compose.yml`-s
- Lihtsat DAG'i: `PythonOperator` (API fetch) + `BashOperator` (`dbt run`, `dbt test`)
- dbt staging → intermediate → marts kihide mõtet
- dbt testide kirjutamist (`schema.yml`)
- Superset'i seadistamist andmebaasiga

**Ei näita** (hoitud lihtsana):
- Airflow TaskFlow API-d ega dynamic task mapping'ut
- dbt makrosid (v.a `generate_schema_name`)
- dbt snapshots / SCD2 mustrit
- Superset'i kasutajate ja rollide haldust
