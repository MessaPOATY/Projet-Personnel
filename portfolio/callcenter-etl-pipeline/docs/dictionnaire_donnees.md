# Dictionnaire de données — entrepôt `centre_contact.duckdb`

## `fait_interactions` — grain : 1 ligne = 1 interaction client

| Colonne | Type | Description | Règle / source |
|---|---|---|---|
| `appel_id` | VARCHAR (PK) | Identifiant unique de l'interaction | `appels.csv`, dédoublonné |
| `date_key` | INTEGER (FK) | Jour de l'interaction au format AAAAMMJJ | dérivé de `date_heure` |
| `heure` | INTEGER | Heure (0-23) | dérivé de `date_heure` |
| `date_heure` | TIMESTAMP | Horodatage de début | 3 formats sources harmonisés |
| `agent_id` | VARCHAR (FK) | Agent ayant traité | NULL si appel abandonné ; doit exister dans `dim_agent` |
| `campagne_id` | VARCHAR (FK) | Campagne / client concerné | |
| `canal` | VARCHAR | `Téléphone`, `Chat`, `Email` | variantes de libellés standardisées |
| `statut` | VARCHAR | `Décroché`, `Abandonné` | |
| `duree_attente_s` | DOUBLE | Attente avant prise en charge (s) | NULL pour l'email (asynchrone) |
| `duree_traitement_s` | DOUBLE | Durée de traitement (s) | ≥ 0, sinon rejet |
| `resolu_1er_contact` | BOOLEAN | Demande résolue dès le 1er contact | `Oui/1/TRUE` → vrai |
| `note_csat` | INTEGER | Note de satisfaction 1 à 5 | NULL si pas de réponse ; hors échelle → rejet |

**Non chargé volontairement :** `numero_client` (donnée personnelle sans utilité analytique — principe de minimisation, art. 5 RGPD).

## `dim_agent`

| Colonne | Description |
|---|---|
| `agent_id` | Identifiant agent (PK) |
| `agent_libelle` | Prénom + initiale du nom (pseudonymisation partielle) |
| `site` | Site de rattachement |
| `equipe` | Niveau 1, Niveau 2, Back-office |
| `date_embauche` | Date d'entrée |

## `dim_campagne`

| Colonne | Description |
|---|---|
| `campagne_id` | Identifiant (PK) |
| `client` | Client donneur d'ordre (fictif) |
| `secteur` | Secteur d'activité |
| `objectif_csat` | Objectif contractuel de satisfaction |

## `dim_date`

Calendrier continu (un jour par ligne, même sans activité) : année, trimestre, mois, semaine ISO, jour de la semaine, indicateur week-end.

## Tables techniques

| Table | Rôle |
|---|---|
| `rejets` | Lignes écartées : source, clé, **motif**, ligne brute, identifiant d'exécution |
| `journal_executions` | Historique des exécutions : volumes, taux de rejet, statut SUCCES / ECHEC |

## Définition des indicateurs (`v_kpi_quotidiens`)

| Indicateur | Définition |
|---|---|
| Taux d'abandon | interactions abandonnées / interactions |
| Attente moyenne | moyenne de `duree_attente_s` |
| DMT | durée moyenne de traitement des interactions décrochées |
| FCR | part des interactions décrochées résolues au 1er contact |
| CSAT moyen | moyenne des notes de satisfaction |
