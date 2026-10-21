-- Chaque interaction n'apparaît qu'une fois dans la table de faits
SELECT interaction_id, COUNT(*) AS n
FROM marts.fct_interactions
GROUP BY interaction_id
HAVING COUNT(*) > 1
