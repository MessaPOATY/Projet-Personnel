-- =====================================================================
-- Modèle en étoile de l'entrepôt "centre de contact" (DuckDB)
-- Grain de la table de faits : 1 ligne = 1 interaction client
-- =====================================================================

-- Rechargement complet idempotent : on supprime d'abord ce qui dépend
-- des dimensions (vue, puis table de faits liée par clés étrangères).
DROP VIEW IF EXISTS v_kpi_quotidiens;
DROP TABLE IF EXISTS fait_interactions;

CREATE OR REPLACE TABLE dim_date (
    date_key      INTEGER PRIMARY KEY,   -- format AAAAMMJJ
    date          DATE NOT NULL,
    annee         INTEGER,
    trimestre     INTEGER,
    mois          INTEGER,
    semaine_iso   INTEGER,
    jour_semaine  VARCHAR,
    est_weekend   BOOLEAN
);

CREATE OR REPLACE TABLE dim_agent (
    agent_id       VARCHAR PRIMARY KEY,
    agent_libelle  VARCHAR,              -- prénom + initiale (minimisation RGPD)
    site           VARCHAR,
    equipe         VARCHAR,
    date_embauche  DATE
);

CREATE OR REPLACE TABLE dim_campagne (
    campagne_id    VARCHAR PRIMARY KEY,
    client         VARCHAR,
    secteur        VARCHAR,
    objectif_csat  DOUBLE,
    date_debut     DATE
);

CREATE OR REPLACE TABLE fait_interactions (
    appel_id            VARCHAR PRIMARY KEY,
    date_key            INTEGER REFERENCES dim_date(date_key),
    heure               INTEGER,
    date_heure          TIMESTAMP,
    agent_id            VARCHAR REFERENCES dim_agent(agent_id),   -- NULL si appel abandonné
    campagne_id         VARCHAR REFERENCES dim_campagne(campagne_id),
    canal               VARCHAR,
    statut              VARCHAR,
    duree_attente_s     DOUBLE,
    duree_traitement_s  DOUBLE,
    resolu_1er_contact  BOOLEAN,
    note_csat           INTEGER CHECK (note_csat BETWEEN 1 AND 5)
);

CREATE OR REPLACE TABLE rejets (
    run_id       VARCHAR,
    source       VARCHAR,
    cle          VARCHAR,
    motif        VARCHAR,
    ligne_brute  VARCHAR
);

CREATE TABLE IF NOT EXISTS journal_executions (
    run_id            VARCHAR PRIMARY KEY,
    debut             TIMESTAMP,
    fin               TIMESTAMP,
    lignes_lues       INTEGER,
    lignes_chargees   INTEGER,
    lignes_rejetees   INTEGER,
    taux_rejet        DOUBLE,
    statut            VARCHAR
);

-- Vue prête pour Power BI : indicateurs quotidiens par campagne
CREATE OR REPLACE VIEW v_kpi_quotidiens AS
SELECT
    d.date,
    c.client,
    f.canal,
    COUNT(*)                                                         AS interactions,
    ROUND(AVG(CASE WHEN f.statut = 'Abandonné' THEN 1.0 ELSE 0 END), 3) AS taux_abandon,
    ROUND(AVG(f.duree_attente_s), 1)                                 AS attente_moy_s,
    ROUND(AVG(f.duree_traitement_s) FILTER (WHERE f.statut = 'Décroché'), 1) AS dmt_s,
    ROUND(AVG(CASE WHEN f.resolu_1er_contact THEN 1.0 ELSE 0 END)
          FILTER (WHERE f.statut = 'Décroché'), 3)                   AS taux_fcr,
    ROUND(AVG(f.note_csat), 2)                                       AS csat_moy
FROM fait_interactions f
JOIN dim_date d     USING (date_key)
JOIN dim_campagne c USING (campagne_id)
GROUP BY ALL;
