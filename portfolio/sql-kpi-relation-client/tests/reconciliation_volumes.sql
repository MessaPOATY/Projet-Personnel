-- Réconciliation : aucune interaction perdue ou dupliquée entre la source et l'agrégat
SELECT brut.n AS volume_source, agrege.n AS volume_mart
FROM (SELECT COUNT(*) AS n FROM raw.interactions) brut,
     (SELECT SUM(volume) AS n FROM marts.mart_kpi_campagne_mensuel) agrege
WHERE brut.n <> agrege.n
