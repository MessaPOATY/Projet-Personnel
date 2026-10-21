-- Performance mensuelle par agent, avec classement au sein de son site.
-- Seuil de 50 interactions : en dessous, un taux n'est pas statistiquement fiable.
WITH base AS (
    SELECT
        mois,
        agent_id,
        site,
        anciennete_mois,
        COUNT(*)                                                AS volume_traite,
        AVG(CASE WHEN est_resolu_reel THEN 1.0 ELSE 0 END)      AS taux_fcr_reel,
        AVG(traitement_s)                                       AS dmt_s,
        AVG(note_csat)                                          AS csat_moyen
    FROM marts.fct_interactions
    WHERE est_traite
    GROUP BY ALL
    HAVING COUNT(*) >= 50
)
SELECT
    *,
    RANK()   OVER (PARTITION BY mois, site ORDER BY taux_fcr_reel DESC) AS rang_fcr_site,
    NTILE(4) OVER (PARTITION BY mois ORDER BY taux_fcr_reel DESC)       AS quartile_fcr,
    taux_fcr_reel - AVG(taux_fcr_reel) OVER (PARTITION BY mois)         AS ecart_moyenne_mois
FROM base
