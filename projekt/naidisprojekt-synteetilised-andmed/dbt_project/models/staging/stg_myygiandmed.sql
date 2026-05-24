-- Puhastab toorandmed: eemaldab vigased read (negatiivsed väärtused),
-- tuletab kuupäeva, kellaaja kategooria ja nädalapäeva.

select
    pood_id,
    mootmise_aeg,
    mootmise_aeg::date                                       as mootmise_kuupaev,
    extract(hour from mootmise_aeg)::integer                 as mootmise_tund,
    extract(dow from mootmise_aeg)::integer                  as nadalapäev_nr,   -- 0=pühapäev, 6=laupäev
    case
        when extract(dow from mootmise_aeg) in (0, 6) then true
        else false
    end                                                      as on_naedavahetus,
    case
        when extract(hour from mootmise_aeg) between  8 and 11 then 'hommik'
        when extract(hour from mootmise_aeg) between 12 and 15 then 'louna'
        when extract(hour from mootmise_aeg) between 16 and 19 then 'parastlouna'
        when extract(hour from mootmise_aeg) between 20 and 21 then 'ohtul'
        else 'muu'
    end                                                      as kellaaeg_kategooria,
    kylastajad,
    kaive_eur,
    genereeritud_kell
from {{ source('staging', 'raw_myygiandmed') }}
where kylastajad > 0
  and kaive_eur  > 0
