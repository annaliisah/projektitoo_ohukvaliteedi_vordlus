# Arhitektuur

> **Juhend:** See fail on projektitöö esimese nädala väljund. Asenda kõik nurksulgudes plankid oma projekti tegeliku sisuga. Kustuta see juhendrida.

## Äriküsimus

Kui hästi kattub mudelipõhine õhukvaliteedi hinnang Eesti seirejaamade tegelike mõõtmistega? 
Projektis võetakse Eesti Keskkonnauuringute Keskuse(EKUK) õhuseire veebilehe ohuseire.ee API-st valitud mõõtejaamadest mõõdetud õhukvaliteedi näitajad, mille põhjal leitakse igale tunnile õhukvaliteedi indeks(link: [placeholder panna KKA link kus on kirjeldatud need parameetrid])
[placeholder md tabel siia]
Peamised viis õhukvliteedi mõõdikut: 
- osakesed (PM2.5 ja PM10),
- troposfääri osoon(O3)
- lämmastikdioksiid(NO2)
- vääveldioksiid(SO2)

Samade parameetrite kohta võetakse mudelarvutatud tulemused OpenMeteo API-st, mis koondab CAMS mudelarvutuse tulemusi. Parameetrid talletatakse samade tundide kohta. 
Andmeid värskendatakse scheduleriga igal täistunnil(võib muutuda olenevalt sellest kuidas andmed päriselt uuenevad). 

Näidikulaual kuvatakse trendidena iga parameetri mõõdetud ja arvutatud väärtused ja õhukvaliteedi indeks valitud ajavahemikus koos nende vahe ja keskmise absoluutveaga(vb ka korrelaatsionikordaja). 

 
## Mõõdikud

1. **Mudelipõhise hinnangu erinevus tegelikest mõõtmistest**  
   Näidikulaual kuvame iga ajahetke ja seirejaama kohta vahe `prognoositud väärtus - mõõdetud väärtus`.

2. **Keskmine absoluutne viga (MAE)**  
   MAE näitab, kui suur on mudelprognoosi tüüpiline viga  mõõdetud õhukvaliteedi näitajaga võrreldes.

$$
MAE = \frac{1}{n} \sum_{i=1}^{n} \left| \hat{y}_i - y_i \right|
$$

   Siin on $\hat{y}_i$ prognoositud väärtus, $y_i$ mõõdetud väärtus ja $n$ vaatluste arv. Mida väiksem on $MAE$, seda lähemal on mudeli hinnangud tegelikele mõõtmistele.

3. **Korrelatsioonikordaja (Pearson $r$)**  
   Pearsoni korrelatsioonikordaja näitab, kui hästi mudel tabab mõõdetud väärtuste ajas muutumise trendi.

$$
r = \frac{\sum_{i=1}^{n} (\hat{y}_i - \bar{\hat{y}})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n} (\hat{y}_i - \bar{\hat{y}})^2}\,\sqrt{\sum_{i=1}^{n} (y_i - \bar{y})^2}}
$$

  $\bar{\hat{y}}$ on prognoositud väärtuste keskmine ja $\bar{y}$ mõõdetud väärtuste keskmine. Mida lähemal on $r$ väärtusele 1, seda paremini tabab mudel mõõdetud väärtuste muutuste trendi ajas.

Täpsustuseks:
### Mõõdetud andmed (Eesti seirejaamad, ohuseire.ee)

- Eestis on **17 õhukvaliteedi seirejaama**
- Valikusse võetakse jaamad, millel on kõik viis parameetrit olemas
- Mõõtmiste intervall: **tunnipõhine, reaalajas**.
- Allikas: `ohuseire.ee` API

### Prognoositud andmed (Open-Meteo Air Quality API, CAMS)

- Allikas: **CAMS European air quality forecast ** Open-Meteo API kaudu.
- Mõõtepunktideks valitakse iga Eesti seirejaama koordinaatidele lähim 11x11 km ruudustikukastike.
- Intervall: **tunnipõhised väärtused**.
- Ajalooline vahemik: `start_date` / `end_date` kaudu, viimaseid x päeva ka `past_days` parameetriga (maksimaalselt 92 päeva võimalik). 
- Päring koordinaatide järgi (jaama lat/lon);  valime lähima ruudustiku punkti.

### Mida millega võrrelda

Iga seirejaama mõõdetud väärtust võrreldakse **sama tunni** Open-Meteo prognoosiga, mis on päritud jaama koordinaatidelt. Võrdlus tehakse ainult **ühiste näitajate** lõikes:
Võrdluse aluseks on **(jaam, näitaja, tund)** ühik: iga selline rida saab kaks väärtust (mõõdetud, prognoositud), mille põhjal arvutame mõõdikud (MAE, Bias, Pearson r).


## Andmeallikad

| Allikas | Tüüp | Ajas muutuv? | Roll |
|---------|------|--------------|------|
| Open-Meteo Air Quality API | API | Jah, iga tund | Mudelprognooside põhiandmevoog |
| Ohuseire.ee mõõteandmed | API | Jah, iga tund | Tegelikud mõõtmised |
| Ohuseire.ee jaamade metaandmed | API | Harva muutuv | Seirejaamade kirjeldused |
| Ohuseire.ee näitajate loend | API | Harva muutuv | Saasteainete ja mõõdikute kirjeldused |

<!-- *- Open-Meteo Air Quality API annab CAMS mudelipõhiseid õhukvaliteedi andmeid. past_days võimaldab küsida kuni 92 päeva tagasi ja start_date / end_date kaudu saab küsida ajaloolist CAMS reanalüüsi. Ohuseire.ee annab Eesti seirejaamade mõõteandmeid JSON-kujul, näiteks jaamad https://www.ohuseire.ee/api/station/et?type=INDICATOR, näitajad https://www.ohuseire.ee/api/indicator/et?type=INDICATOR ja mõõtmised https://www.ohuseire.ee/api/monitoring/et?....* -->

## Andmevoog - TODO 

```mermaid
flowchart LR
    source[ohuseire.ee API] --> ingest[Sissevõtt(Python)]
    source2[Open-Meteo Forecast API] --> ingest
    ingest --> staging[(staging(PostgresSQL db)]
    staging --> transform[Transformatsioon]
    transform --> mart[(mart)]
    mart --> dashboard[Näidikulaud]
    mart --> quality[Andmekvaliteedi testid]
    scheduler[Scheduler(nt APScheduler)] --> ingest
```

> Täpsusta diagrammi vastavalt oma projektile — lisa rohkem andmeallikaid, mudeleid või teenuseid.

## Andmebaasi kihid

| Kiht | Roll |
|------|------|
| `staging` | Hoiab allika andmeid töötlemata kujul. |
| `mart` | Hoiab transformeeritud ja ärilogikat sisaldavaid tabeleid. |

## Tööjaotus

| Roll | Vastutus | Täitja |
|------|----------|--------|
| Andmeallika omanik | Kirjutab sissevõtu loogika, hoiab API-t töös | Liivika/Anna-Liisa |
| Transformatsioonide omanik | Kirjutab mart kihi mudelid ja mõõdikute arvutuse | Liivika/Anna-Liisa |
| Kvaliteedi omanik | Kirjutab testid ja vaatab läbi ebaõnnestunud kontrollid | Kristen/Heigo |
| Näidikulaua omanik | Ehitab näidikulaua ja seob selle äriküsimusega | Kristen/Heigo |

## Riskid - TODO 

| Risk | Mõju | Maandus |
|------|------|---------|
| [Risk 1 — näiteks: API ei vasta] | Mõõteandmed ei tule üle |  |
| [Risk 2] | [Mis juhtub?] | [Kuidas maandad?] |
| [Risk 3] | [Mis juhtub?] | [Kuidas maandad?] |

## Privaatsus ja turve - TODO

[Kirjelda, millised isiku- või tundlikud andmed teie projektis esinevad (kui üldse) ja kuidas neid kaitsete. Isikuandmed peavad olema anonümiseeritud. Andmebaasi paroolid peavad tulema `.env` failist.]
