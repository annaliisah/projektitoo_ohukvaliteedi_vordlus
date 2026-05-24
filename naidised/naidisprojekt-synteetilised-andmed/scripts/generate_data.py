"""
Sünteetiliste müügiandmete generaator — EstiMüük OÜ näidisandmed

PEDAGOOGILINE EESMÄRK
─────────────────────
See skript näitab, kuidas luua statistiliselt usaldusväärne sünteetiline andmestik
olukordadeks, kus päris andmeid ei saa avaliku repoga jagada. Generaatorkood on
läbipaistev — igaüks saab näha, kuidas mustrid on loodud, ja seda kohandada.

Genereerib N päeva tunnipõhiseid müügiandmeid 8 fiktiivsele EstiMüük OÜ kauplusele.
Realistlikud mustrid:
  - Lahtiolekuajad (8–22 tundi)
  - Lõuna tipp (12–14) ja pärastlõuna tipp (17–19)
  - Nädalavahetuse kõrgem külastatavus (+30%)
  - Kaupluse-spetsiifiline baasmaht (suured kauplused rohkem külastajaid)
  - Juhuslik müra (±20%)

Kasutamine:
  python scripts/generate_data.py [--days 90] [--seed 42] [--reset]
"""

import argparse
import os
from datetime import datetime, timedelta, timezone

import numpy as np
import psycopg2

# Fiktiivsete kaupluste seadistus
# Iga kauplus on EstiMüük OÜ ühe kujuteldava harukaupluse näide.
KAUPLUSED = [
    {"pood_id": "tallinn_kesklinn",   "baas_kylastajad": 45, "baas_kaive": 32.0},
    {"pood_id": "tallinn_lasnamae",   "baas_kylastajad": 38, "baas_kaive": 26.5},
    {"pood_id": "tartu_lõunakeskus",  "baas_kylastajad": 35, "baas_kaive": 28.0},
    {"pood_id": "parnu_rannapark",    "baas_kylastajad": 22, "baas_kaive": 24.0},
    {"pood_id": "narva_astri",        "baas_kylastajad": 18, "baas_kaive": 21.0},
    {"pood_id": "viljandi_centrum",   "baas_kylastajad": 15, "baas_kaive": 22.5},
    {"pood_id": "kuressaare_market",  "baas_kylastajad": 12, "baas_kaive": 23.0},
    {"pood_id": "haapsalu_promenaad", "baas_kylastajad": 10, "baas_kaive": 21.5},
]

# Tunnipõhised kordajad (indeks = tund, 0 = kinnine)
TUNNI_KORDAJAD = [
    0, 0, 0, 0, 0, 0, 0, 0,   # 0–7  suletud
    0.4, 0.6, 0.8, 1.0,        # 8–11 hommik
    1.6, 1.8, 1.4, 1.2,        # 12–15 lõunatipp
    1.3, 1.7, 1.5, 1.2,        # 16–19 pärastlõunatipp
    0.9, 0.6, 0, 0,            # 20–23 õhtu + suletud
]

NAEDAVAHETUSE_KORDAJA = 1.3   # laupäev ja pühapäev
MÜRA_PROTSENT = 0.20           # ±20% juhuslik kõikumine


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "analytics-db"),
        port=int(os.environ.get("DB_PORT", 5432)),
        user=os.environ.get("DB_USER", "praktikum"),
        password=os.environ.get("DB_PASSWORD", "praktikum"),
        dbname=os.environ.get("DB_NAME", "praktikum"),
    )


def genereeri_read(days: int, seed: int) -> list[tuple]:
    """Genereerib (pood_id, mootmise_aeg, kylastajad, kaive_eur) tuple'ite nimekirja."""
    rng = np.random.default_rng(seed)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    algusmomment = now - timedelta(days=days)

    read = []
    t = algusmomment
    while t <= now:
        tund = t.hour
        on_naedavahetus = t.weekday() >= 5  # 5=laupäev, 6=pühapäev
        tunni_kordaja = TUNNI_KORDAJAD[tund]

        if tunni_kordaja == 0:
            t += timedelta(hours=1)
            continue

        for kauplus in KAUPLUSED:
            kordaja = tunni_kordaja * (NAEDAVAHETUSE_KORDAJA if on_naedavahetus else 1.0)
            müra = 1.0 + rng.uniform(-MÜRA_PROTSENT, MÜRA_PROTSENT)

            kylastajad = max(1, int(kauplus["baas_kylastajad"] * kordaja * müra))

            # Käive = külastajad × keskmine ostukorv ± müra
            ostukorv_müra = 1.0 + rng.uniform(-MÜRA_PROTSENT, MÜRA_PROTSENT)
            kaive = round(kylastajad * kauplus["baas_kaive"] * ostukorv_müra, 2)

            read.append((
                kauplus["pood_id"],
                t.replace(tzinfo=None),  # timestamp ilma tzinfo'ta (DB column on timestamp)
                kylastajad,
                kaive,
            ))

        t += timedelta(hours=1)

    return read


def laadi_andmebaasi(read: list[tuple], reset: bool = False) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if reset:
                cur.execute("TRUNCATE TABLE staging.raw_myygiandmed")
                print("Olemasolevad andmed kustutatud.")

            cur.executemany(
                """
                INSERT INTO staging.raw_myygiandmed
                    (pood_id, mootmise_aeg, kylastajad, kaive_eur)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (pood_id, mootmise_aeg) DO NOTHING
                """,
                read,
            )
            conn.commit()
            print(f"Laaditud {cur.rowcount} uut rida.")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Genereeri sünteetilisi müügiandmeid.")
    parser.add_argument("--days",  type=int, default=int(os.environ.get("SYNTH_DAYS", 90)),
                        help="Mitu päeva minevikku genereerida (vaikimisi: 90)")
    parser.add_argument("--seed",  type=int, default=int(os.environ.get("SYNTH_RANDOM_SEED", 42)),
                        help="Juhusliku generaatori seeme (vaikimisi: 42)")
    parser.add_argument("--reset", action="store_true",
                        help="Kustuta olemasolevad andmed enne lisamist")
    args = parser.parse_args()

    print(f"Genereerime {args.days} päeva müügiandmeid (seed={args.seed})...")
    read = genereeri_read(days=args.days, seed=args.seed)
    print(f"Genereeritud {len(read)} rida ({len(KAUPLUSED)} kauplust).")

    laadi_andmebaasi(read, reset=args.reset)
    print("Valmis!")


if __name__ == "__main__":
    main()
