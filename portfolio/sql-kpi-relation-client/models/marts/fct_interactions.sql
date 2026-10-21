-- Couche MARTS : table de faits enrichie, prête pour Power BI.
SELECT
    i.*,
    c.client,
    c.secteur,
    a.site,
    a.anciennete_mois,
    r.est_reitere_7j,
    -- FCR « réel » : résolu ET sans recontact du client sous 7 jours
    (i.est_resolu AND NOT COALESCE(r.est_reitere_7j, FALSE)) AS est_resolu_reel
FROM staging.stg_interactions i
JOIN staging.stg_campagnes c USING (campagne_id)
LEFT JOIN staging.stg_agents a USING (agent_id)
LEFT JOIN intermediate.int_reiterations r USING (interaction_id)
