-- Question : le taux de résolution déclaré par les agents est-il fiable ?
-- On le compare au FCR « réel » (sans recontact du client sous 7 jours).
-- Techniques : agrégats filtrés, comparaison à un objectif via jointure
SELECT
    client,
    ROUND(100 * AVG(taux_fcr_declare), 1)                      AS fcr_declare_pct,
    ROUND(100 * AVG(taux_fcr_reel), 1)                         AS fcr_reel_pct,
    ROUND(100 * AVG(taux_fcr_declare - taux_fcr_reel), 1)      AS ecart_pts,
    ROUND(100 * MAX(objectif_fcr), 0)                          AS objectif_pct,
    SUM(CASE WHEN fcr_atteint THEN 1 ELSE 0 END) || ' / ' || COUNT(*) AS mois_objectif_atteint
FROM marts.mart_kpi_campagne_mensuel
GROUP BY client
ORDER BY ecart_pts DESC
