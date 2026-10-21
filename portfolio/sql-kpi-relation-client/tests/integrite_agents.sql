-- Toute interaction traitée est rattachée à un agent connu du référentiel
SELECT f.interaction_id, f.agent_id
FROM marts.fct_interactions f
LEFT JOIN staging.stg_agents a USING (agent_id)
WHERE f.est_traite AND a.agent_id IS NULL
