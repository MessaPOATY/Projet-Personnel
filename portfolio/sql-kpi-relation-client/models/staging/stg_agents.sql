SELECT
    agent_id,
    site,
    CAST(date_embauche AS DATE) AS date_embauche,
    -- Ancienneté figée à la fin de la période étudiée (30/06/2026)
    DATE_DIFF('month', CAST(date_embauche AS DATE), DATE '2026-06-30') AS anciennete_mois
FROM raw.agents
