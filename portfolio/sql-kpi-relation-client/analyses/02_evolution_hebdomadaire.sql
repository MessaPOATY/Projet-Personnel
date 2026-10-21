-- Question : comment évoluent les volumes semaine après semaine ?
-- Techniques : LAG (variation vs semaine précédente), moyenne mobile sur 4 semaines
WITH hebdo AS (
    SELECT semaine, COUNT(*) AS volume,
           ROUND(AVG(note_csat), 2) AS csat
    FROM marts.fct_interactions
    GROUP BY semaine
    HAVING COUNT(DISTINCT date_interaction) = 7   -- semaines complètes uniquement
)
SELECT
    semaine,
    volume,
    ROUND(100.0 * (volume - LAG(volume) OVER w) / LAG(volume) OVER w, 1) AS variation_pct,
    ROUND(AVG(volume) OVER (w ROWS BETWEEN 3 PRECEDING AND CURRENT ROW), 0) AS moyenne_mobile_4s,
    csat
FROM hebdo
WINDOW w AS (ORDER BY semaine)
ORDER BY semaine
