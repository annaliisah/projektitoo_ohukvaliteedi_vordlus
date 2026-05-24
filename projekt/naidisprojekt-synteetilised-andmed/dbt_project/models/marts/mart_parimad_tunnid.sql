-- Parimate kellaajatundide analüüs kaupluste lõikes.
-- Näitab, mis tunnil on keskmiselt kõrgeim müügitõhusus.
-- Kasutatav Supersetis kellaajamustrite visualiseerimiseks.

select
    pood_id,
    pood_nimi,
    linn,
    mootmise_tund,
    kellaaeg_kategooria,
    count(*)                                          as mootmisi,
    round(avg(kylastajad), 1)                         as kesk_kylastajad,
    round(avg(kaive_eur), 2)                          as kesk_kaive_eur,
    round(avg(kaive_kylastaja_kohta), 2)              as kesk_tohusus,
    round(
        avg(kaive_kylastaja_kohta) filter (where on_naedavahetus = false), 2
    )                                                 as kesk_tohusus_toopaev,
    round(
        avg(kaive_kylastaja_kohta) filter (where on_naedavahetus = true), 2
    )                                                 as kesk_tohusus_naedavahetus

from {{ ref('int_myyk_tunnipohine') }}
group by pood_id, pood_nimi, linn, mootmise_tund, kellaaeg_kategooria
order by pood_id, mootmise_tund
