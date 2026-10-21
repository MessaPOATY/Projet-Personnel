-- Un abandon n'a ni agent, ni durée de traitement, ni résolution
SELECT interaction_id
FROM marts.fct_interactions
WHERE est_abandonne
  AND (agent_id IS NOT NULL OR traitement_s > 0 OR est_resolu IS NOT NULL)
