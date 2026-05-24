-- Arvutab müügitõhususe iga tunni ja kaupluse kohta.
-- Tõhusus = käive / külastaja (kui palju üks külaline keskmiselt kulutab).

select
    s.pood_id,
    s.mootmise_aeg,
    s.mootmise_kuupaev,
    s.mootmise_tund,
    s.on_naedavahetus,
    s.kellaaeg_kategooria,
    s.kylastajad,
    s.kaive_eur,
    round(s.kaive_eur / nullif(s.kylastajad, 0), 2)  as kaive_kylastaja_kohta,

    -- Kategoriseeri tõhusus
    case
        when (s.kaive_eur / nullif(s.kylastajad, 0)) >= 30 then 'Kõrge'
        when (s.kaive_eur / nullif(s.kylastajad, 0)) >= 20 then 'Keskmine'
        else 'Madal'
    end                                               as tohususe_tase,

    -- Poe meta
    p.pood_nimi,
    p.linn,
    p.maakond,
    p.poe_suurus_m2

from {{ ref('stg_myygiandmed') }} s
left join {{ ref('pood') }} p
    on s.pood_id = p.pood_id
