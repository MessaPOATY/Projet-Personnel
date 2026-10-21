-- Question : l'ancienneté des agents influence-t-elle la résolution et la satisfaction ?
-- (piste pour cibler les actions de formation des nouveaux arrivants)
-- Techniques : CASE de segmentation, agrégation
SELECT
    CASE
        WHEN anciennete_mois < 12 THEN '1. moins de 1 an'
        WHEN anciennete_mois < 24 THEN '2. 1 à 2 ans'
        WHEN anciennete_mois < 36 THEN '3. 2 à 3 ans'
        ELSE                           '4. plus de 3 ans'
    END                                                     AS tranche_anciennete,
    COUNT(DISTINCT agent_id)                                AS agents,
    COUNT(*)                                                AS interactions,
    ROUND(100 * AVG(CASE WHEN est_resolu_reel THEN 1.0 ELSE 0 END), 1) AS fcr_reel_pct,
    ROUND(AVG(traitement_s) / 60, 1)                        AS dmt_min,
    ROUND(AVG(note_csat), 2)                                AS csat_moyen
FROM marts.fct_interactions
WHERE est_traite
GROUP BY 1
ORDER BY 1
