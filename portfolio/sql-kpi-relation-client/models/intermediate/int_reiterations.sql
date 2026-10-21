-- Couche INTERMEDIATE : logique métier réutilisable.
--
-- Réitération : un client qui recontacte la même campagne dans les 7 jours
-- signale souvent que sa demande n'a PAS vraiment été résolue la première fois,
-- même si l'agent l'a déclarée « résolue ». C'est un contrôle de fiabilité du FCR déclaratif.
WITH contacts AS (
    SELECT
        interaction_id,
        client_id,
        campagne_id,
        horodatage,
        LEAD(horodatage) OVER (
            PARTITION BY client_id, campagne_id
            ORDER BY horodatage
        ) AS prochain_contact
    FROM staging.stg_interactions
    WHERE est_traite
)
SELECT
    interaction_id,
    prochain_contact,
    COALESCE(prochain_contact <= horodatage + INTERVAL 7 DAY, FALSE) AS est_reitere_7j
FROM contacts
