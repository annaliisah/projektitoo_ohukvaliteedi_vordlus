-- Päevane müügikokkuvõte kaupluse kohta: käive, külastajad, tõhusus, soovitus.

select
    pood_id,
    pood_nimi,
    linn,
    maakond,
    mootmise_kuupaev,
    on_naedavahetus,
    count(*)                                          as avatud_tunde,
    sum(kylastajad)                                   as kylastajaid_kokku,
    round(sum(kaive_eur), 2)                          as kaive_kokku_eur,
    round(avg(kaive_kylastaja_kohta), 2)              as kesk_tohusus,
    max(kaive_kylastaja_kohta)                        as max_tohusus,
    round(avg(kylastajad), 1)                         as kesk_kylastajad_tunnis,
    -- Päevane tõhususe hinnang
    case
        when round(avg(kaive_kylastaja_kohta), 2) >= 28 then 'Kõrge'
        when round(avg(kaive_kylastaja_kohta), 2) >= 22 then 'Keskmine'
        else 'Madal'
    end                                               as paevane_tohususe_tase

from {{ ref('int_myyk_tunnipohine') }}
group by pood_id, pood_nimi, linn, maakond, mootmise_kuupaev, on_naedavahetus
