-- Question : qui sont les 3 meilleurs agents de chaque site sur le dernier mois ?
-- (identifier des « référents » pour le tutorat des nouveaux arrivants)
-- Techniques : sous-requête scalaire, RANK + filtre direct sur la fenêtre (QUALIFY)
SELECT
    site,
    RANK() OVER (PARTITION BY site ORDER BY taux_fcr_reel DESC) AS rang,
    agent_id,
    anciennete_mois,
    volume_traite,
    ROUND(100 * taux_fcr_reel, 1)                AS fcr_reel_pct,
    ROUND(100 * ecart_moyenne_mois, 1)           AS ecart_moyenne_pts,
    ROUND(csat_moyen, 2)                         AS csat
FROM marts.mart_performance_agent_mensuel
WHERE mois = (SELECT MAX(mois) FROM marts.mart_performance_agent_mensuel)
QUALIFY rang <= 3
ORDER BY site, rang
