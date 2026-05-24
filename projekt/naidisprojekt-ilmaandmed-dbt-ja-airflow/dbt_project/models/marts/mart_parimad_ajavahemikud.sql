-- Leiab parimad 3-tunnised ajaaknad välitegevuseks (ainult päevasel ajal).
-- Kasutab libisevat 3-tunni akent, mis arvutab keskmise skoori kolme järjestikuse
-- tunni jooksul. Tagastab ainult aknad, kus kesk_skoor >= 50.

with libisev_aken as (
    select
        run_id,
        asukoha_id,
        asukoha_nimi,
        prognoos_aeg                                                as vahemiku_algus,
        prognoos_aeg + interval '3 hours'                          as vahemiku_lopp,
        prognoos_kuupaev,

        round(avg(koguskoor) over (
            partition by run_id, asukoha_id
            order by prognoos_aeg
            rows between current row and 2 following
        ), 1) as kesk_skoor,

        round(sum(sademed_mm) over (
            partition by run_id, asukoha_id
            order by prognoos_aeg
            rows between current row and 2 following
        ), 1) as sademed_3h_mm,

        round(max(tuulekiirus_ms) over (
            partition by run_id, asukoha_id
            order by prognoos_aeg
            rows between current row and 2 following
        ), 1) as max_tuul_ms,

        round(avg(temperatuur_c) over (
            partition by run_id, asukoha_id
            order by prognoos_aeg
            rows between current row and 2 following
        ), 1) as kesk_temp_c,

        sum(on_paev) over (
            partition by run_id, asukoha_id
            order by prognoos_aeg
            rows between current row and 2 following
        ) as paeva_tunde

    from {{ ref('int_ilmaandmed_skoor') }}
    where on_paev = 1
)

select
    run_id,
    asukoha_id,
    asukoha_nimi,
    vahemiku_algus,
    vahemiku_lopp,
    prognoos_kuupaev,
    kesk_skoor,
    sademed_3h_mm,
    max_tuul_ms,
    kesk_temp_c,
    paeva_tunde,
    case
        when kesk_skoor >= 80 then 'Väga sobiv'
        when kesk_skoor >= 60 then 'Sobiv'
        else 'Piiripealne'
    end as soovitus

from libisev_aken
where kesk_skoor >= 50
order by kesk_skoor desc
