-- Question : à quels moments de la semaine la charge est-elle la plus forte,
-- et quel impact sur le respect du SLA ?  (aide au dimensionnement des plannings)
-- Techniques : agrégation conditionnelle, pivot manuel
SELECT
    heure,
    ROUND(AVG(nb) FILTER (WHERE jour_semaine_num = 1), 0) AS lundi,
    ROUND(AVG(nb) FILTER (WHERE jour_semaine_num = 2), 0) AS mardi,
    ROUND(AVG(nb) FILTER (WHERE jour_semaine_num = 3), 0) AS mercredi,
    ROUND(AVG(nb) FILTER (WHERE jour_semaine_num = 4), 0) AS jeudi,
    ROUND(AVG(nb) FILTER (WHERE jour_semaine_num = 5), 0) AS vendredi,
    ROUND(100 * AVG(sla), 1)                              AS sla_pct
FROM (
    SELECT date_interaction, jour_semaine_num, heure,
           COUNT(*)                                          AS nb,
           AVG(CASE WHEN sla_respecte THEN 1.0 ELSE 0 END)   AS sla
    FROM marts.fct_interactions
    WHERE jour_semaine_num <= 5 AND canal <> 'Email'
    GROUP BY ALL
)
GROUP BY heure
ORDER BY heure
