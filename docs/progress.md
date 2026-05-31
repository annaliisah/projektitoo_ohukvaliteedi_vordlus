# Edenemisraport

> **Juhend:** See fail on projektitöö teise nädala väljund. Uuenda lühidalt iga esitamise eel. Kustuta see juhendrida.

## Mis on valmis

- [x] Docker Compose käivitab kõik teenused - Postgres + ETL pipeline + Streamlit dashboard
- [x] Andmeid saadakse kahest allikast kätte - Andmeid saadakse kahest allikast: ohuseire.ee monitoring API ja Open-Meteo Air Quality API (CAMS)
- [x] Andmed laetakse `staging` kihti - `staging.ohuseire_monitoring_raw`, `staging.openmeteo_airquality_raw`
- [x] Vähemalt üks transformatsioon toimib - Transformatsioon `staging → mart.fact_air_quality_observation` (ajavööndite normaliseerimine UTC-sse, mõõteinstrumendi nullpunkti müra puhastus - miinusmärgiga väikesed mõõtmised teisendatakse nulliks, sest kontsentratsioon ei saa olla negatiivne)
- [x] Vähemalt üks näidikulaud on nähtaval - Streamlit näidikulaud http://localhost:8501 — KPI (keskmine MAE), MAE tabel indikaatori kaupa, mõõdetud vs prognoositud ajagraafik
- [x] Vähemalt üks andmekvaliteedi test läbib (4 andmekvaliteedi testi (`scripts/quality_tests.sql`))

- [x] Pipeline run audit logitakse tabelisse `staging.pipeline_runs`, sissevõtt on idempotentne.
- [x] Lisaks Sprint 1 plaanile on tehtud: eksperimenteeriv notebook (`notebooks/01_ohuseire.ipynb`) API-de tundma õppimiseks ja uuritud mõlema API andmeid. Praeguste andmetega (Õismäe jaam, viimased 7 päeva, 5 indikaatorit): 920 mõõdetud + 960 prognoositud rida marti kihis. MAE: SO₂ 0.23, NO₂ 1.44, O₃ 5.95, PM10 3.01, PM2.5 0.94 µg/m³.

## Järgmised sammud

- [Esimene tegevus, mis ees ootab]
- [Teine tegevus]
- [Kolmas tegevus]

## Mis takistab

- [Probleem 1 — näiteks: API tagastab vigaseid väärtusi ühes linnas]
- [Probleem 2 — või: "Praegu pole blokeerivaid probleeme"]

## Kontrollpunkt

Käsk, millega saab kontrollida, et töövoog töötab:

```bash
# [Lisa siia käsk, mis näitab, et andmed liiguvad allikast näidikulauani]
# Näiteks:
docker compose exec pipeline python scripts/run_pipeline.py check
```

Oodatav tulemus: [Kirjelda, mida töötav süsteem väljastab]
