-- Loob skeemid ja sünteetiliste andmete toorandmete tabelid.
-- Generaator (scripts/generate_data.py) kirjutab staging.raw_myygiandmed tabelisse.
-- dbt loob ülejäänud tabelid ja vaated ise.

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;

-- Tunnipõhised müügiandmed (genereeritud sünteetiliselt)
CREATE TABLE IF NOT EXISTS staging.raw_myygiandmed (
    pood_id           text         NOT NULL,
    mootmise_aeg      timestamp    NOT NULL,
    kylastajad        integer      NOT NULL,
    kaive_eur         numeric(10,2) NOT NULL,
    genereeritud_kell timestamptz  NOT NULL DEFAULT now(),
    PRIMARY KEY (pood_id, mootmise_aeg)
);
