# Näidisprojekt: Sünteetilised andmed — EstiMüük OÜ müügitõhusus

See näidisprojekt on mõeldud gruppidele, kes soovivad analüüsida **tööandja äriprobleemi**,
kuid ei saa tundlikke andmeid avaliku repoga jagada. Näide näitab, kuidas luua
statistiliselt usaldusväärne sünteetiline andmestik ja ehitada selle peale täielik pipeline.

## Stsenaarium

> **EstiMüük OÜ** on kaheksa kauplusega fiktiivsete kaupluste kett. Ärianalüütika tiim
> soovib mõista, millistes kauplustes ja mis kellaaegadel on müügitõhusus kõrgeim.
>
> Pärisandmed sisaldavad klientide isikuteavet ja konfidentsiaalset hinnainfot, mida
> ei saa avaliku repoga jagada. Seetõttu lõi tiim statistiliselt samaväärse
> **sünteetilise andmestiku** (`scripts/generate_data.py`), mis jäljendab pärisandmete
> struktuuri ja hooajalisi mustreid, kuid ei sisalda ühtegi päris tehingut ega klienti.

## Äriküsimus

Millistes kauplustes ja mis kellaaegadel on müügitõhusus (käive külastaja kohta) kõrgeim?

**Mõõdikud:**
1. Müügitõhusus (€/külaline) kaupluse ja kellaaja lõikes
2. Päevane käive ja külastatavus kaupluse kohta
3. Kellaaegade mustrid — hommik, lõuna, pärastlõuna

## Andmestik

| Allikas | Tüüp | Ajas muutuv? | Roll |
|---------|------|--------------|------|
| `scripts/generate_data.py` | Python-generaator (numpy) | Ei, genereeritakse ühekorra (90 päeva fikseeritud seemnega) | Sünteetilised tunnipõhised müügimõõtmised |
| `seeds/pood.csv` | Staatiline dbt seed | Ei, muutub ainult projekti muutmisel | Kaupluste meta-andmed (nimi, linn, suurus) |

## Stack

| Komponent | Tööriist |
|-----------|---------|
| Andmegeneraator | Python + numpy |
| Orkestreerimine | Apache Airflow 3.x |
| Transformatsioon | dbt Core 1.10 |
| Andmehoidla | PostgreSQL (pgDuckDB) |
| Näidikulaud | Apache Superset 6.x |

## Andmevoog lühidalt

1. **Genereerimine** — Airflow DAG kontrollib, kas `staging.raw_myygiandmed` on tühi. Kui jah, käivitab `generate_data.py`, mis genereerib 90 päeva tunnipõhised müügiandmed 8 kaupluse kohta.
2. **Laadimine** — Generaator kirjutab andmed `staging.raw_myygiandmed` tabelisse (ON CONFLICT DO NOTHING — korduvkäivitused ei kahekordista andmeid).
3. **Transformatsioon** — `dbt run` ehitab staging vaate → intermediate tõhususe vaate → marts kokkuvõttetabelid.
4. **Testimine** — `dbt test` kontrollib 7 andmekvaliteedi testi (not_null, accepted_values).
5. **Näidikulaud** — Superset loeb `marts.*` tabeleid ja näitab kaupluste paremusjärjestust, kellaajamustrit ja KPI-d.

## Projekti struktuur

```
.
├── compose.yml                    ← kõik teenused
├── .env.example                   ← kopeeri .env-iks
├── .gitignore
├── Dockerfile.superset
├── scripts/
│   ├── generate_data.py           ← PEAMINE: sünteetiliste andmete generaator
│   └── import_dashboard.sh
├── airflow/
│   └── dags/
│       └── myygipipeline.py       ← Airflow DAG (generate → dbt run → dbt test)
├── dbt_project/
│   ├── seeds/
│   │   └── pood.csv               ← 8 fiktiivsed kauplused
│   ├── models/
│   │   ├── staging/               ← 1 mudel + testid
│   │   ├── intermediate/          ← 1 mudel + testid
│   │   └── marts/                 ← 2 mudelit + testid
│   └── macros/
├── init/
│   └── 01_create_schemas.sql
├── superset/
│   ├── superset_config.py
│   └── dashboards/
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

# 4. Oota ~2–3 minutit
docker compose ps   # kõik peaksid olema "running"

# 5. Käivita Airflow UI-s DAG käsitsi esimesel korral
#    http://localhost:8080  (kasutaja/parool: vt .env AIRFLOW_USER/PASSWORD)
#    → myyk_pipeline → "Trigger DAG"
#    DAG genereerib 90 päeva sünteetilised andmed ja käivitab dbt.

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
| `SYNTH_DAYS` | Mitu päeva sünteetilisi andmeid genereerida (vaikimisi 90) |
| `SYNTH_RANDOM_SEED` | Generaatori seeme — sama seeme annab alati sama andmestiku (vaikimisi 42) |

## Andmekvaliteedi testid

dbt testid käivituvad automaatselt iga DAG-käivituse lõpus (`dbt test`).

1. `staging.stg_myygiandmed` — kriitilised veerud ei ole NULL (`pood_id`, `mootmise_aeg`, `kylastajad`, `kaive_eur`)
2. `staging.stg_myygiandmed` — `kellaaeg_kategooria` on lubatud väärtuste hulgas ('hommik', 'louna', 'parastlouna', 'ohtul', 'muu')
3. `intermediate.int_myyk_tunnipohine` — `kaive_kylastaja_kohta` ei ole NULL
4. `intermediate.int_myyk_tunnipohine` — `tohususe_tase` on lubatud väärtuste hulgas ('Kõrge', 'Keskmine', 'Madal')
5. `marts.mart_pood_paevane` — `kesk_tohusus` ja `paevane_tohususe_tase` ei ole NULL
6. `marts.mart_pood_paevane` — `paevane_tohususe_tase` on lubatud väärtuste hulgas
7. `marts.mart_parimad_tunnid` — `kesk_tohusus` ei ole NULL

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
- `marts` → `mart_pood_paevane`
- `marts` → `mart_parimad_tunnid`

### 3. Loo chart'id

**Charts → + Chart** → vali dataset → vali chart tüüp → seadista → **Create chart** → Save.

> Kui Superset lisab automaatselt ajafiltri, jäta see `No filter` olekusse — eemaldada ei saa, aga `No filter` tähendab, et kõik andmed on nähtaval.

**Chart 1 — Kaupluste paremusjärjestus**
- Tüüp: **Bar Chart**, dataset: `mart_pood_paevane`
- **X-axis**: `pood_nimi`
- **Metrics**: `kesk_tohusus` (AVG)
- **X-Axis Sort By**: `AVG(kesk_tohusus)` + lülita sisse **Sort Descending**

**Chart 2 — Kellaajamustrid**
- Tüüp: **Line Chart**, dataset: `mart_parimad_tunnid`
- **X-axis**: `mootmise_tund`
- **Metrics**: `kesk_tohusus` (AVG)
- **Dimensions** (series): `pood_nimi`

**Chart 3 — KPI — kõrgeim tõhusus**
- Tüüp: **Big Number**, dataset: `mart_pood_paevane`
- **Metric**: `max_tohusus` (MAX)

### 4. Loo dashboard

**Dashboards → + Dashboard** → anna nimi (nt "EstiMüük OÜ — müügitõhusus") → lohista chart'id paika → Publish.

### 5. Ekspordi dashboard (ZIP reposse)

```bash
docker compose exec superset superset export-dashboards \
  -f /app/dashboards/myyk_dashboard.zip

docker compose cp superset:/app/dashboards/myyk_dashboard.zip \
  superset/dashboards/myyk_dashboard.zip
```

### 6. Impordi dashboard (kui ZIP on juba reposis)

```bash
bash scripts/import_dashboard.sh
```

## Kokkuvõte, puudused ja võimalikud edasiarendused

**Mis töötab:**
- Pipeline töötab end-to-end: genereerimine → staging → dbt → Superset
- Generaator on reprodutseeritav (fikseeritud seeme) — sama `SYNTH_RANDOM_SEED` annab alati sama andmestiku
- DAG on idempotentne — korduvkäivitused ei kahekordista andmeid

**Teadlikud piirangud:**
- Superset dashboard tuleb esimesel korral käsitsi seadistada
- Genereeritud mustrid on lihtsustatud (lõunatipp, nädalavahetus) — reaalse äri keerukust ei jäljenda täielikult
- Generaator ei tekita sesoonset variatsiooni (suvine vs. talvine periood)

**Võimalikud edasiarendused:**
- Lisa sesoonset variatsiooni generaatorisse (`MONTH_MULT` sõnastik nagu moodul 09 näites)
- Kohandada kaupluste nimekirja ja mustreid oma valdkonna järgi
- Automatiseerida Superset'i datasettide ja chart'ide loomine skriptiga

## Sünteetiliste andmete lähenemine

`scripts/generate_data.py` genereerib 90 päeva müügiandmeid kaheksa kaupluse kohta.

**Kuidas mustrid on ehitatud:**
- Lahtiolekuajad: 8–22 tundi (väljaspool seda `TUNNI_KORDAJA = 0`)
- Lõunatipp (12–14h): 1,6–1,8× baasmaht
- Nädalavahetus: 1,3× baasmaht
- Juhuslik müra: ±20%

**Kohandamine oma projekti jaoks:**
```python
# Muuda KAUPLUSED nimekirjas baas_kylastajad ja baas_kaive oma valdkonna järgi
# Muuda TUNNI_KORDAJAD oma äri töögraafiku järgi
# Muuda NAEDAVAHETUSE_KORDAJA ja MÜRA_PROTSENT vastavalt vajadusele
```

Rohkem infot: [`docs/arhitektuur.md`](docs/arhitektuur.md)
