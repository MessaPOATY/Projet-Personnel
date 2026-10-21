-- Les taux calculés sont des proportions valides
SELECT mois, campagne_id
FROM marts.mart_kpi_campagne_mensuel
WHERE NOT (taux_abandon BETWEEN 0 AND 1)
   OR NOT (taux_sla BETWEEN 0 AND 1)
   OR NOT (taux_fcr_reel BETWEEN 0 AND 1)
   OR taux_fcr_reel > taux_fcr_declare      -- le FCR réel ne peut pas dépasser le FCR déclaré
