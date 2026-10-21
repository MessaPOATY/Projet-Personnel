-- Couche STAGING : typage explicite, renommage, colonnes dérivées simples.
-- Aucune règle métier complexe ici : on « met au propre » la source.
SELECT
    interaction_id,
    CAST(horodatage AS TIMESTAMP)                     AS horodatage,
    CAST(horodatage AS DATE)                          AS date_interaction,
    DATE_TRUNC('month', CAST(horodatage AS DATE))     AS mois,
    DATE_TRUNC('week',  CAST(horodatage AS DATE))     AS semaine,
    EXTRACT(hour FROM CAST(horodatage AS TIMESTAMP))  AS heure,
    ISODOW(CAST(horodatage AS DATE))                  AS jour_semaine_num,   -- 1 = lundi
    client_id,
    campagne_id,
    canal,
    agent_id,
    CAST(attente_s AS DOUBLE)                         AS attente_s,
    CAST(traitement_s AS DOUBLE)                      AS traitement_s,
    CAST(abandonne AS BOOLEAN)                        AS est_abandonne,
    NOT CAST(abandonne AS BOOLEAN)                    AS est_traite,
    CAST(resolu AS BOOLEAN)                           AS est_resolu,
    CAST(note_csat AS INTEGER)                        AS note_csat,
    -- SLA : interaction synchrone traitée en moins de 60 s d'attente
    CASE WHEN canal = 'Email' THEN NULL
         ELSE (NOT CAST(abandonne AS BOOLEAN) AND attente_s <= 60)
    END                                               AS sla_respecte
FROM raw.interactions
