-- Päevane kokkuvõte iga asukoha kohta: maksimaalne ja keskmine skoor,
-- temperatuur, sademete kogus, riskitase.

select
    run_id,
    asukoha_id,
    asukoha_nimi,
    prognoos_kuupaev,
    count(*)                                                as prognoosi_tunde,
    round(avg(koguskoor), 1)                               as kesk_skoor,
    max(koguskoor)                                         as max_skoor,
    round(avg(temperatuur_c), 1)                           as kesk_temp_c,
    max(temperatuur_c)                                     as max_temp_c,
    round(sum(sademed_mm), 1)                              as kokku_sademed_mm,
    round(max(tuulekiirus_ms), 1)                          as max_tuul_ms,
    sum(case when on_paev = 1 then 1 else 0 end)           as paevasel_ajal_tunde,
    case
        when max(koguskoor) >= 80 then 'Väga sobiv'
        when max(koguskoor) >= 60 then 'Sobiv'
        when max(koguskoor) >= 40 then 'Piiripealne'
        else 'Ebasoodne'
    end                                                    as paeva_soovitus

from {{ ref('int_ilmaandmed_skoor') }}
group by run_id, asukoha_id, asukoha_nimi, prognoos_kuupaev
