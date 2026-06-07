# Edenemisraport

## Mis on valmis

- [x] Docker Compose käivitab kõik teenused - Postgres + ETL pipeline + Streamlit dashboard
- [x] Andmeid saadakse kahest allikast kätte - Andmeid saadakse kahest allikast: ohuseire.ee monitoring API ja Open-Meteo Air Quality API (CAMS)
- [x] Andmed laetakse `staging` kihti - `staging.ohuseire_monitoring_raw`, `staging.openmeteo_airquality_raw`
- [x] Vähemalt üks transformatsioon toimib - Transformatsioon `staging → mart.fact_air_quality_observation` (ajavööndite normaliseerimine UTC-sse, mõõteinstrumendi nullpunkti müra puhastus - miinusmärgiga väikesed mõõtmised teisendatakse nulliks, sest kontsentratsioon ei saa olla negatiivne)
- [x] Vähemalt üks näidikulaud on nähtaval - Streamlit näidikulaud http://localhost:8501 — KPI (keskmine MAE), MAE tabel indikaatori kaupa, mõõdetud vs prognoositud ajagraafik
- [x] Vähemalt üks andmekvaliteedi test läbib (4 andmekvaliteedi testi (`scripts/quality_tests.sql`))
---

- [x] Pipeline run audit logitakse tabelisse `staging.pipeline_runs`, sissevõtt on idempotentne.
- [x] Lisaks Sprint 1 plaanile on tehtud: eksperimenteeriv notebook (`notebooks/01_ohuseire.ipynb`) API-de tundma õppimiseks ja uuritud mõlema API andmeid. Praeguste andmetega (Õismäe jaam, viimased 7 päeva, 5 indikaatorit): 920 mõõdetud + 960 prognoositud rida marti kihis. MAE: SO₂ 0.23, NO₂ 1.44, O₃ 5.95, PM10 3.01, PM2.5 0.94 µg/m³.

## Järgmised sammud

- pipeline ühtlustada
- kvaliteedikontrolli ja transformatsiooni skripte täiendada
- lisada paar seirejaama juurde
- lisada pikema ajavahemiku ajalugu
- README ja kasutusjuhend lõpetada


## Mis takistab

- blokeerivaid probleeme ei ole (peale ajapuuduse), tuleb edasi pingutada

## Kontrollpunkt

Käsk, millega saab kontrollida, et töövoog töötab:

```bash
cp .env.example .env
docker compose up -d --build
# oota ~30 sek
docker compose logs pipeline --tail 20
# ava http://localhost:8501
```

Oodatav tulemus: pipeline logide lõpus `==> Pipeline lõpetatud`, brauseris dashboard 4 elemendiga (KPI, MAE tabel, ajagraafik, kvaliteedi testid).


---

## Sprint 3  (07.06.2026)

### Mis sai valmis sprindi jooksul

- [x] **Pipeline ühtlustatud** — `scripts/run_pipeline.sh` käivitab kõik sammud järjest (seed_dimensions → fetch_ohuseire_monitoring → fetch_openmeteo_airquality → transform.sql → quality_tests.sql) ja logib iga jooksu.
- [x] **Andmevoog terviklik** — mõlemad allikad (Ohuseire.ee monitoring API, Open-Meteo Air Quality API) töötavad ja salvestavad staging kihti, transformatsioon teisendab need mart kihti.
- [x] **Mart kihi laiendus** — lisaks faktitabelile `mart.fact_air_quality_observation` on nüüd 6 analüüsivaadet:
  - `fact_air_quality_comparison` — mõõdetud vs prognoositud samal real;
  - `fact_pollutant_index` — EEA indeksi tase 1–6 üksiku saasteaine kohta;
  - `fact_air_quality_index` — üldindeks per jaam ja tund (halvim üksiku saasteaine tase);
  - `fact_air_quality_metrics` — MAE, bias, korrelatsioon per jaam + saasteaine;
  - `fact_hourly_error` — keskmine viga ööpäeva tunni kaupa;
  - `fact_index_match` — kas mõõdetud ja prognoositud indeks klapivad samal tunnil.
- [x] **Õhukvaliteedi indeks lisatud** — kasutusel EEA European Air Quality Index 6-tasemeline skaala (1=Hea ... 6=Eriti halb), katab kõik 5 saasteainet (SO₂, NO₂, O₃, PM10, PM2.5). Piirväärtused defineeritud SQL-is (`transform.sql`).
- [x] **Dashboard viimistletud** — kõik äriloogika viidud mart kihti, dashboard teeb ainult `SELECT`-e. Põhigraafikul on joone värv vastav indeksi tasemele (piiripunktidesse interpoleeritud), eraldi sektsioon üldindeksi võrdluseks (mõõdetud vs prognoositud + KPI-d).
- [x] **Andmekvaliteedi testid** — 4 testi (negatiivsed väärtused, primaarvõtme unikaalsus, iga fact rea indicator_id dim_indicator-is, mõõtmise värskus).
- [x] **README täiendatud** — kõik malli sektsioonid täidetud, täielik `.env` muutujate tabel, andmevoo selgitus, indeksi tabel ja  "Puudused" loend.

### Puudused

- Demo keskendub ühele jaamale (Õismäe), kuigi pipeline toetab mitut.
- Kõrgemad indeksi tasemed (3–6) jäid praeguses andmestikus realiseerimata, kuna Õismäe õhk on puhas.

### Mis edasi (kui projekti edasi arendaks)

- Rohkem jaamu + Eesti kaardivaade.
- Pikem ajalooline ulatus + trendianalüüs.
- Eraldi orkestreerija (Airflow cron'i asemel.
- Rohkem mõõdikuid 
