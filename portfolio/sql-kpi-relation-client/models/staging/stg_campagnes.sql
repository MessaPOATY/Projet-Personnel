SELECT
    campagne_id,
    client,
    secteur,
    CAST(objectif_sla AS DOUBLE) AS objectif_sla,
    CAST(objectif_fcr AS DOUBLE) AS objectif_fcr
FROM raw.campagnes
