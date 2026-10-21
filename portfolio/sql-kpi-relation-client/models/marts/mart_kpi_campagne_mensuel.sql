-- KPI mensuels par campagne, comparés aux objectifs contractuels.
WITH kpi AS (
    SELECT
        mois,
        campagne_id,
        client,
        COUNT(*)                                                    AS volume,
        AVG(CASE WHEN est_abandonne THEN 1.0 ELSE 0 END)            AS taux_abandon,
        AVG(CASE WHEN sla_respecte THEN 1.0 ELSE 0 END)
            FILTER (WHERE sla_respecte IS NOT NULL)                 AS taux_sla,
        AVG(CASE WHEN est_resolu THEN 1.0 ELSE 0 END)
            FILTER (WHERE est_traite)                               AS taux_fcr_declare,
        AVG(CASE WHEN est_resolu_reel THEN 1.0 ELSE 0 END)
            FILTER (WHERE est_traite)                               AS taux_fcr_reel,
        AVG(traitement_s) FILTER (WHERE est_traite)                 AS dmt_s,
        AVG(note_csat)                                              AS csat_moyen,
        COUNT(note_csat)                                            AS nb_reponses_csat
    FROM marts.fct_interactions
    GROUP BY ALL
)
SELECT
    k.*,
    c.objectif_sla,
    c.objectif_fcr,
    k.taux_sla >= c.objectif_sla       AS sla_atteint,
    k.taux_fcr_reel >= c.objectif_fcr  AS fcr_atteint
FROM kpi k
JOIN staging.stg_campagnes c USING (campagne_id)
ORDER BY mois, campagne_id
