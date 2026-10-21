-- Question : quelles campagnes ne tiennent pas leur engagement de service, et combien de mois d'affilée ?
-- Techniques : « gaps and islands » (séquences consécutives) avec ROW_NUMBER
WITH statut AS (
    SELECT client, mois, taux_sla, objectif_sla, sla_atteint,
           ROW_NUMBER() OVER (PARTITION BY client ORDER BY mois)
         - ROW_NUMBER() OVER (PARTITION BY client, sla_atteint ORDER BY mois) AS groupe
    FROM marts.mart_kpi_campagne_mensuel
)
SELECT
    client,
    ROUND(100 * AVG(taux_sla), 1)                         AS sla_moyen_pct,
    ROUND(100 * MAX(objectif_sla), 0)                     AS objectif_pct,
    COUNT(*) FILTER (WHERE NOT sla_atteint)               AS mois_en_echec,
    MAX(serie) FILTER (WHERE NOT sla_atteint)             AS plus_longue_serie_echec
FROM (
    SELECT *, COUNT(*) OVER (PARTITION BY client, sla_atteint, groupe) AS serie
    FROM statut
)
GROUP BY client
ORDER BY sla_moyen_pct
