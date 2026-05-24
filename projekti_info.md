# projektitöö ja sprintide info

# Teema püstitus - Priit Adler

## Õhukvaliteedi mudelprognoosi ja seirejaama mõõtmiste võrdlus
- e-mail - priit.adler@ut.ee
- Tase - eelistus puudub
- Teema pealkiri - Õhukvaliteedi mudelprognoosi ja seirejaama mõõtmiste võrdlus
- Äriküsimus - Kui hästi kattub mudelipõhine õhukvaliteedi hinnang Eesti seirejaamade tegelike mõõtmistega?
- Andmeallikad ja nende muutuvus ajas - Open-Meteo Air Quality API annab CAMS mudelipõhiseid õhukvaliteedi andmeid. past_days võimaldab küsida kuni 92 päeva tagasi ja start_date / end_date kaudu saab küsida ajaloolist CAMS reanalüüsi. Ohuseire.ee annab Eesti seirejaamade mõõteandmeid JSON-kujul, näiteks jaamad https://www.ohuseire.ee/api/station/et?type=INDICATOR, näitajad https://www.ohuseire.ee/api/indicator/et?type=INDICATOR ja mõõtmised https://www.ohuseire.ee/api/monitoring/et?....
- Andmete jagatavus avalikud
- Mitut grupi liiget otsite? - 4: olen mentor, ei osale ise grupitöös
- Lisamärkused - Näidikulaud võiks näidata mõõdetud väärtust, mudelväärtust, nende vahet ja keskmist absoluutset viga.

# sprint 2

... 

# sprint 1

## Eesmärk
Selle sprindi lõpuks on grupil paigas projekti suund: kokku lepitud äriküsimus, kaardistatud andmeallikad, joonistatud arhitektuur ja jagatud tööjaotus. Lisaks olete teinud esimesed tehnilised katsetused, et veenduda, kas ligipääsud, API-d ja tööriistad töötavad.

Selle sprindi eesmärk ei ole ehitada toimivat töövoogu. Eesmärk on välistada üllatused enne, kui hakkate koodi kirjutama.

## Tegevused nädala jooksul
1. **Leppige kokku äriküsimus**. Üks lause, mis ütleb, mida soovite andmetest teada saada. Lisaks 2–3 mõõdikut või küsimust, mida näidikulaud näitab.
2. **Kaardistage andmeallikad**. Vähemalt üks põhiallikas peab olema ajas muutuv (API, kasvav andmebaas, regulaarselt uuenev fail). Staatiline CSV peamise allikana ei sobi. Kontrollige praktikas, kas ligipääsud toimivad.
3. **Joonistage arhitektuuriskeem**. Allikast lõpptulemini. Sobib Mermaid, draw.io, Excalidraw või käsitsi joonis + foto.
4. **Jagage tööülesanded**. Iga grupiliige saab konkreetse vastutusala (näiteks andmeallika omanik, transformatsioonide omanik, kvaliteedi omanik, näidikulaua omanik).
5. **Tuvastage 2–3 peamist riski**. Mis võib teie projektis pooleli jätta? Kuidas neid maandate?
6. **Tehke esimesed tehnilised katsetused**. Kas API vastab? Kas saate andmebaasiga ühenduda? Kas valitud tööriistad jooksevad?

## Mida esitada
### Grupitöö (üks esitus grupi kohta)
Moodle assignmentis "Sprint 1 esitus (grupitöö)":
- Repo link (GitHub eelistatud)
- Kinnitus, et failis docs/arhitektuur.md on täidetud kõik järgnevad sektsioonid:
  - Äriküsimus
  - Mõõdikud
  - Andmeallikad
  - Andmevoog (skeem)
  - Andmebaasi kihid
  - Tööjaotus
  - Riskid
  - Privaatsus ja turve

Mall on GitHub repos `ut-andmeinseneeria-2026`. Kopeerige see oma repo `docs/` kausta ja täitke.

Kui repo on privaatne, lisage juhendajatele ligipääs (kasutajanimed leiate samast GitHub repost).

### Individuaalne (iga osaleja eraldi)
Moodle assignmentis "Sprint 1 esitus (individuaalne)". 3-4 küsimust, võtab umbes 5 minutit, nähtav ainult juhendajatele.

## Hindamine
Sprint 1 esituse osas vaatame järgnevat:
- Äriküsimus on selge. Konkreetne, mõõdetav, üks lause.
- Andmeallikad sobivad. Vähemalt üks ajas muutuv. Ligipääs on praktikas kontrollitud.
- Arhitektuur on usutav. Skeemilt on aru saada, kust andmed tulevad ja kuhu lähevad.
- Tööjaotus on selge. Iga liige teab oma vastutust.
- Riskid on identifitseeritud. 2–3 peamist riski koos maandamisega.

Selle sprindi esitust eraldi arvestatud või mittearvestatud hindega ei märgita. See on sisend lõpparvestusse ja eeldus järgmiseks sprindiks. Tagasiside `docs/arhitektuur.md` osas tuleb sprindi 2 jooksul.

## Ootused failile `docs/arhitektuur.md`
Mall sisaldab kõik vajalikud sektsioonid. Mõned täpsustused:
- **Mõõdikud**: kirjeldage iga mõõdiku arvutusvalem sõnadega. Mitte ainult nimi.
- **Andmeallikad**: "ajas muutuv" tähendab seda, et andmed lisanduvad või muutuvad regulaarselt. Märkige, kui sageli (näiteks "iga 15 minuti tagant", "kord päevas").
- **Andmevoog**: Mermaid skeem on lihtsaim, sest renderdub otse GitHubis. Aga sobib ka pilt.
- **Tööjaotus**: iga roll peaks olema täidetud. Üks inimene võib täita mitut rolli, kui grupp on väiksem.
- **Riskid**: mõelge realistlikud. "API võib aeglane olla" pole risk, "API andmeid uuendatakse ainult kord nädalas, mis ei näita ajas muutuvust" on risk.
- **Privaatsus ja turve**: ka avalike andmete puhul kirjeldage lühidalt, kuidas hoiate ligipääsuvõtmeid. Eelistatud .env + .env.example repos.

## Sagedased küsimused
**Mis siis, kui pole jõudnud kõike teha 24.05-ks?** Esitage see, mis on valmis. Hilinenud esitused võtame vastu, aga märkige docs/arhitektuur.md failis, mis on veel lahtine. Sprindi 3 viimane tähtaeg on ainus, mis on lukus.

**Kas peame valima lõpliku tehnoloogiavirna kohe? **Ei. Kursuse vaikevalik (PostgreSQL, dbt, Airflow, Superset) sobib enamikele projektidele. Kui te kahtlete, märkige praegune eelistus ja viimistlege sprindi 2 ajal. Kui kasutate alternatiivset virna (näiteks Microsoft Fabric, Snowflake), märkige see ja põhjendage lühidalt.

**Kas peame andmeallika juba pärima tegelikult andmetega?** Sprindi 1 lõpuks piisab, kui olete kontrollinud, et ligipääs töötab (näiteks teinud ühe testpäringu, mille vastus on salvestatud). Tegelik korduv pärimine on sprindi 2 ülesanne.

**Mis kella aja järgi käib tähtaeg**? Eesti aja järgi (Europe/Tallinn). Moodle kasutab teie konto seadeid, vaikimisi on see Eesti aeg.

## Abi
Üldised küsimused: Moodle foorum "Projektitöö küsimused"
Konkreetne mentorlus: broneerimise link
Kui broneerimises pole vabu aegu, andke meilile märku



# Projektitöö info

## Eesmärk
Projektitöö raames ehitate grupis (3-4 inimest) ühe otsast-lõpuni andmetöövoo:
andmete sissevõtt,
transformatsioon,
kvaliteedikontroll ja
näidikulaud (dashboard). 

Eelistatud on, et lahendate päris probleemi, mis on grupile või kellegi tööandjale tegelikult kasulik. Aga võib vabalt ka teha töö avalikult kättesaadavate andmete ja väljamõeldud probleemi lahendamisega.

Sisuline projektitöö kestab 3 nädalat (18.05 - 07.06). Projektitöö igal nädalal on vahepealsed väljundid mida tuleb Moodle-s esitada. Projektitöö viimasel nädalal on vaja esitada **GitHub repositoorium** ja **video** (kuni 10 minutit) kus teete oma lahendusest esitluse ja lühikese demo. 08.06 - 14.06 annate individuaalset tagasisidet teistele gruppidele.

Eraldi kaitsmisi või kontakttunde vahemikus 18.05 - 14.06 **ei toimu**. Küll aga on võimalik küsida küsimusi ning broneerida videokõnet mentorluseks.

## 1. Milline projekt olema peaks
### Kohustuslikud nõuded
1. **Selge äriküsimus**. Üks lause, mis ütleb, mida andmetest soovitakse teada saada. 2-3 mõõdikut või küsimust, mida näidikulaud näitaks.
2. **Vähemalt üks põhiandmevoog peab tulema ajas muutuvast andmeallikast.** API, mida saab korduvalt pärida, andmebaas, kuhu lisandub kirjeid, või regulaarselt uuenev fail. Staatiline CSV-fail ei sobi peamise andmeallikana. Kõrvaltabelitena (nt dbt seed-id riigikoodide, valuutade, kategooriate jaoks) on staatilised CSV-d täiesti lubatud ja loomulikud.
3. **Automatiseeritud andmete sissevõtt.** Kood, mis on käivitatav ja korratav (mitte käsitsi import).
4. **Vähemalt üks transformatsioonisamm.** Toorandmed muudetakse analüüsiks sobivaks (nt kasutades medaljoni arhitektuuri ja dimensionaalset mudeldamist).
5. **Andmekvaliteedi testid.** Vähemalt 3 testi (nt unikaalsed väärtused, not null, väärtuste vahemik, jne).
6. **Näidikulaud.** Vähemalt 2 KPI-d või visuaali, mis vastavad äriküsimusele.
7. **Saladused .env-failis,** mitte koodis. .env.example repos, päris .env .gitignore-s.
8. **README ette antud malli põhjal.** Sisaldab äriküsimust, arhitektuuri, juhiseid käivitamiseks.
### Tööriistade valik on vaba
Kursuses õpetatud tehnoloogiavirn (stack) on vaikimisi soovitus ja saate selle kasutamisel kõige detailsema tagasiside. Lubatud on ka Microsoft Fabric, Snowflake, Prefect, Dagster, Power BI, Metabase ja muud. Asendusi ei pea eraldi kinnitama. Kõik 8 kohustuslikku nõuet (vt eespool) kehtivad sõltumata tööriistade valikust.

AGA: kui kasutate teistsuguseid tööriistu, siis peate arvestama et juhendajate tagasiside võib olla pinnapealsem.

### Andmed ja privaatsus
- **Avalikud andmed:** kõik lubatud, repo võib olla avalik.
- **Tööandja andmed:** veenduge, et tööandja lubab kasutada. Tundlikud andmed ei tohi sattuda GitHubi (.gitignore, anonüümitud näidised).
- **Konfidentsiaalsed andmed:** kasutage anonüümitud või sünteetilist versiooni, mis võimaldab jagada andmeid ka grupis sees.
### Üksi tegemine
Vaikimisi tehakse projekti grupis. Üksi tegemine on erand ja vajab juhendajatega eelnevat kokkulepet.

## 2. Mida hinnatakse
Hindamine on **arvestatud / mittearvestatud**. Juhendajad hindavad video ja repo põhjal. Lisaks on igal osalejal vaja teha tagasiside kahele grupile (vt allpool).

### Arvestuse saamise tingimused
1. Grupp on esitanud nõuetekohase projekti (8 kohustuslikku nõuet, vt eelmist osa).
2. Grupp on esitanud iganädalased väljundid Moodle-s (iga projektitöö nädala lõpus).
3. Iga osaleja on esitanud 3 individuaalset vahetagasiside vormi (iga projektitöö nädala lõpus).
4. Iga osaleja on tagasisidestanud 2 teise grupi tööd (08.06 - 14.06).
5. Süstemaatilise mittepanustamise korral võib individuaalne arvestus jääda saamata.
### Hindamise kriteeriumid
Juhendajad hindavad järgnevat. Need on samad kriteeriumid, mille järgi te annate tagasisidet teistele gruppidele.

1. **Äriküsimus ja väärtus.** Kas äriküsimus on selge ja kas näidikulaud vastab sellele.
2. **Andmevoog.** Kas andmetoru on terviklik ja ajas muutuvus tuleb välja.
3. **Andmekvaliteet.** Kas testid katavad olulisi probleeme.
4. **Tehniline lahendus.** Kas tehnoloogiavalikud on põhjendatud ja töövoog idempotentne.
5. **Selgus ja esitlus.** Kas video ja README on arusaadavad ka väljaspool gruppi olijale.
6. **Refleksioon.** Mida grupp tegi hästi, mida saaks teistelt õppida.

### Vahetagasiside sisu (igal nädalal sama vorm)
Iga vahetagasiside on individuaalne, konfidentsiaalne ja võtab 5 minutit. Vorm on Moodle assignmentis ja sisaldab kolme küsimust:

1. Mida sina sel nädalal konkreetselt tegid? (3-5 punkti, lühidalt)
2. Kuidas hindad teiste grupiliikmete panust? (võrdne / suurem / väiksem, lühike kommentaar)
3. Kas on midagi, mida juhendaja peaks teadma? (vaba tekst, pole kohustuslik)
Vastused on nähtavad ainult juhendajatele, mitte teistele grupiliikmetele.

|nädal|   |
|---|---|
|   |   |
svsv|sgsg
jsja|kka

## 3. Mida pead nelja nädala jooksul tegema
Ajakava
Nädal	|Põhitegevus	|Tähtaeg	|Vaja esitada
|---|---|---|---|
18.05 - 24.05	|Planeerimine ja arhitektuur. Esimesed katsed andmeallikatega.	|P 23:59	|(a) repo link, `docs/arhitektuur.md` repos (grupitöö) <br>(b) Vahetagasiside #1 (individuaalne).
25.05 - 31.05	|Esmane töötav minimaalne otsast lõpuni töövoog: üks allikas → üks transformatsioon → üks visuaal.	|P 23:59	|(a) Töötav minimaalne töövoog repos + `docs/progress.md`. (grupitöö)  <br>(b) Vahetagasiside #2 (individuaalne).
01.06 - 07.06	|Lõpetamine: kõik allikad, testid, näidikulaud, README, video.	|P 23:59	|(a) Täielik projekt repos. (grupitöö) <br>(b) Video YouTube'is (unlisted). (grupitöö) <br>(c) Linkide esitamine Moodle assignmentis. (grupitöö) <br>(d) Vahetagasiside #3. (individuaalne)
08.06 - 14.06	|Tagasiside teistele gruppidele.	|P 23:59	|Tagasiside 2 teise grupi tööle Moodle assignmentis. (individuaalne)

### 18.05 - 24.05: Planeerimine ja arhitektuur

**Mida teete:**
- Lepite kokku äriküsimuse ja mõõdikud.
- Kaardistate andmeallikad ja kontrollite, et ligipääsud töötavad.
- Joonistate arhitektuuriskeemi.
- Jagate ülesanded grupiliikmete vahel.
- Alustate esimeste tehniliste katsetustega (kas API töötab, kas saame andmebaasi ühenduda).

**Mida esitate (24.05. P 23:59):**
1. Repos fail `docs/arhitektuur.md`, mis sisaldab:
   - Äriküsimust ja 2-3 mõõdikut.
   - Arhitektuuriskeemi (Mermaid, Excalidraw, draw.io, käsitsi joonis + foto).
   - Andmeallikate loetelu ja muutuvuse kirjeldust.
   - Tööjaotust (kes mille eest vastutab).
   - 2-3 riski.
2. Individuaalne vahetagasiside Moodle assignmentis (5 minutit, konfidentsiaalne).


### 25.05 - 31.05: Esimene töötav andmevoog

**Mida teete:**
- Ehitate ühe andmevoo täielikult välja: üks allikas, andmete sissevõtt, üks transformatsioon, üks visuaal.
- Selle eesmärk: leida tehnilised probleemid varakult.
- Pole vaja, et oleks olemas kõik allikad ja kõik testid. Oluline näha, kus tekivad võimalikud pudelikaelad.

**Mida esitate (31.05 P 23:59):**
1. Repos:
   - Toimiv kood (vähemalt üks allikas → transformatsioon → visuaal).
   - Fail `docs/progress.md` (5 rida): mis on valmis, mis on järgmised sammud, mis takistab.
2. Individuaalne vahetagasiside Moodle assignmentis.

### 01.06 - 07.06: Projekti lõpetamine

**Mida teete:**
- Lisate puuduvad andmeallikad ja transformatsioonid.
- Kirjutate andmekvaliteedi testid (vähemalt 3 tk).
- Viimistlete näidikulauda (vähemalt 2 KPI-d).
- Täidate README ette antud malli põhjal.
- Salvestate 10-minutilise video (esitlus + demo).

**Mida esitate (07.06 P 23:59):**

1. Repos:
    - Täielik projekt vastavalt 8 kohustuslikule nõudele.
    - Täidetud README malli põhjal.
2. Video: 10 minutit, jagatud lingi kaudu (nt YouTube unlisted, Google Drive, Onedrive).
3. Moodle assignment: link videole, link repole. Kui repo on privaatne, lisage juhendajatele ligipääs.
4. Individuaalne vahetagasiside Moodle assignmentis.

### 08.06 - 14.06: Tagasiside teistele 

**Mida teete:**
- Hiljemalt esmaspäeva hommikul saate Moodle's teada, mis 2 grupi videot ja repot teil tagasisidestada tuleb.
- Vaatate videod, sirvite repod.
- Esitate tagasiside Moodle assignmentis.

**Mida esitate (14.06 P 23:59):**
Iga grupi kohta vastate 6 punktile. Iga vastus peab olema sisuline ja konkreetne, viidates just selle grupi tööle. Üldised vastused ("tubli", "hea töö") ei kvalifitseeru ja palutakse ümber teha.

1. **Äriküsimus ja väärtus.** Kas grupi äriküsimus on selge ja kas dashboard vastab sellele? Kas kasutaksid päriselt?
2. **Andmevoog.** Kas andmetoru on terviklik (allikad → transformatsioon → dashboard)? Kas ajas muutuvus tuleb välja?
3. **Andmekvaliteet.** Kas testid katavad olulisi probleeme? Mis võiks veel lisada?
4. **Tehniline lahendus.** Mis tundus tark valik? Mis oleks ise teisiti teinud?
5. **Selgus ja esitlus.** Kas video on arusaadav? Mis jäi segaseks?
6. **Mida tegi see grupp paremini? Mida saaks see grupp teie grupilt õppida? **Kahepoolne refleksioon, konkreetsed asjad.


**Näide heast vastusest punktile 3:**

> Olemas on null-, unique- ja accepted_values testid. Hea, et on ka custom test "tellimuse summa peab olema positiivne". Lisaks võiks olla värskuse test, mis kontrollib, et viimane kirje pole vanem kui 24 tundi.

**Näide ebapiisavast vastusest:**

> Andmekvaliteet on hea ja testid katavad kõik olulise.

## Mida peab esitama? Detailid

- **Video**: 10 minutit, jagatud lingi kaudu (YouTube unlisted, Google Drive, Onedrive - ükskõik milline, peaasi et link on vaadatav ilma sisselogimata), link Moodle assignmentis.
- **Repo**: GitHub eelistatud, teised platvormid juhendaja kinnitusel.
- **Repo nähtavus**: avalik on soovitatav. Privaatne on lubatud, kuid sel juhul peab grupp videos näitama oma koodi struktuuri, peamisi transformatsioone ja andmekvaliteedi teste, et tagasisidestajad saaksid hinnata tehnilist lahendust ja andmekvaliteeti.
- **Privaatse repo korral** lisada juhendajatele ligipääs (kasutajanimed leiate GitHub repos `ut-andmeinseneeria-2026`).


## Tugi ja küsimused
- **Foorum Moodle's:** "Projektitöö küsimused". Postita küsimus uue arutelu-postitusena. Kui Moodle teated e-mailile segavad, siis on võimalik tellimuse seada päevaseks kokkuvõtteks (Profiil → Eelistused → Foorumi sätted).
- **15-minutilised konsultatsioonid**: saab broneerida Moodle's oleva lingi kaudu, link lisandub mai keskel.
- **README mall ja näidisprojektid**: GitHubi repos `ut-andmeinseneeria-2026` (link Moodle's, näidised lisanduvad mai alguses).

## Sagedased küsimused
**Mis juhtub, kui keegi grupis ei panusta?**
Vahetagasisidetes on koht, kus teised liikmed saavad sellest juhendajale teada anda. Süstemaatilise mittepanustamise korral võib selle inimese individuaalne arvestus jääda saamata, isegi kui grupp esitab korrektse projekti.

**Kas grupp võib olla suurem kui 4?**
Vaikimisi mitte. Erandid juhendaja kinnitusel.

**Mis juhtub, kui ma ei jõua mõnda vahesammu tehtud õigeks ajaks?**
Oluline on, et projektitöö esitamine (07.06 23:59) ei hilineks. Muud hilinemised mõned tunnid või 1 päev on andestatavad, kui need pole süstemaatilised. Hilinenud vahesammud vaadatakse läbi, aga süstemaatiline hilinemine mõjutab arvestust.