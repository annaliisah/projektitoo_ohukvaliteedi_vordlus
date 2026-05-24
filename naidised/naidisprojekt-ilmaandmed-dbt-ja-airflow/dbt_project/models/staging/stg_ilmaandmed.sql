-- Puhastab toorandmed: eemaldab puuduvaid väärtusi sisaldavad read,
-- standardiseerib veerunimed ja tuletab kuupäeva ja tunni.

select
    run_id,
    asukoha_id,
    asukoha_nimi,
    laiuskraad,
    pikkuskraad,
    prognoos_aeg::timestamp                             as prognoos_aeg,
    prognoos_aeg::date                                  as prognoos_kuupaev,
    extract(hour from prognoos_aeg::timestamp)::integer as prognoos_tund,
    temperatuur_c,
    sademed_mm,
    sademe_toenaosus_pct,
    tuulekiirus_ms,
    on_paev,
    laetud_kell
from {{ source('staging', 'ilmaandmed_raw') }}
where temperatuur_c           is not null
  and sademed_mm              is not null
  and tuulekiirus_ms          is not null
  and sademe_toenaosus_pct    is not null
