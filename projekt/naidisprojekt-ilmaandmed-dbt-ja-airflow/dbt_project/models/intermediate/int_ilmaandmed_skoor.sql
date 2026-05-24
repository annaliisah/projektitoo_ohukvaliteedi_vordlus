-- Arvutab iga tunniprognoosi kohta välitegevuse sobivusskoori (0–100).
--
-- Punktisüsteem:
--   Temperatuur  (0–30 p): optimaalne 16–24°C
--   Sademed      (0–35 p): mida vähem sademeid ja mida madalam tõenäosus, seda parem
--   Tuul         (0–25 p): optimaalne alla 4 m/s
--   Päevavalgus  (0–10 p): päevasel ajal 10 punkti, öösel 0

with baas as (
    select
        run_id,
        asukoha_id,
        asukoha_nimi,
        prognoos_aeg,
        prognoos_kuupaev,
        prognoos_tund,
        temperatuur_c,
        sademed_mm,
        sademe_toenaosus_pct,
        tuulekiirus_ms,
        on_paev,

        case
            when temperatuur_c between 16 and 24 then 30
            when temperatuur_c between 10 and 30 then 15
            else 0
        end as temp_skoor,

        case
            when sademed_mm = 0 and sademe_toenaosus_pct <= 20 then 35
            when sademed_mm <= 0.5 and sademe_toenaosus_pct <= 40 then 20
            when sademed_mm <= 2 then 10
            else 0
        end as sademe_skoor,

        case
            when tuulekiirus_ms <= 4  then 25
            when tuulekiirus_ms <= 8  then 15
            when tuulekiirus_ms <= 12 then 5
            else 0
        end as tuule_skoor,

        case when on_paev = 1 then 10 else 0 end as paevavalguse_skoor

    from {{ ref('stg_ilmaandmed') }}
)

select
    *,
    (temp_skoor + sademe_skoor + tuule_skoor + paevavalguse_skoor) as koguskoor,

    case
        when (temp_skoor + sademe_skoor + tuule_skoor + paevavalguse_skoor) >= 80 then 'Väga sobiv'
        when (temp_skoor + sademe_skoor + tuule_skoor + paevavalguse_skoor) >= 60 then 'Sobiv'
        when (temp_skoor + sademe_skoor + tuule_skoor + paevavalguse_skoor) >= 40 then 'Piiripealne'
        else 'Ebasoodne'
    end as sobivuse_silt,

    case
        when sademed_mm > 2                then 'Palju sademeid'
        when tuulekiirus_ms > 12           then 'Tugev tuul'
        when on_paev = 0                   then 'Öine aeg'
        when temperatuur_c < 10
          or temperatuur_c > 30            then 'Sobimatu temperatuur'
        else                                    'Sobivad tingimused'
    end as peamine_pohjus

from baas
