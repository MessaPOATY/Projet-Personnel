# Fiche de traitement — Analyse des motifs de réclamation clients

*Générée automatiquement le 21/10/2026 à 18:10*

## 1. Description du traitement

| | |
|---|---|
| **Finalité** | Identifier les principaux motifs d'insatisfaction et suivre les délais de traitement afin d'améliorer la qualité de service. Aucune décision individuelle n'est prise sur la base de ce jeu de données. |
| **Base légale** | Intérêt légitime (art. 6.1.f RGPD) |
| **Responsable** | Direction Relation Client (fictif) |
| **Destinataires** | Équipe Data — usage analytique uniquement |
| **Durée de conservation** | 24 mois à compter de la clôture de la réclamation |

## 2. Données traitées et mesures appliquées

| Colonne source | DCP détectée | Mesure | Colonne en sortie | Justification |
|---|---|---|---|---|
| `reclamation_id` | — | conserver | `reclamation_id` | Clé technique sans lien direct avec la personne |
| `date_reclamation` | — | conserver | `date_reclamation` | Nécessaire au suivi des délais |
| `client_id` | identifiant_indirect (indirect) | pseudonymiser | `client_pseudo` | Permet de compter les réclamations d'un même client sans l'identifier |
| `nom` | identifiant_direct (direct) | supprimer | *(supprimée)* | Inutile à la finalité (minimisation) |
| `prenom` | identifiant_direct (direct) | supprimer | *(supprimée)* | Inutile à la finalité (minimisation) |
| `email` | email (direct) | supprimer | *(supprimée)* | Inutile à la finalité (minimisation) |
| `telephone` | telephone (direct) | supprimer | *(supprimée)* | Inutile à la finalité (minimisation) |
| `iban_remboursement` | iban (sensible) | supprimer | *(supprimée)* | Donnée financière, aucun usage analytique |
| `numero_secu` | nir (sensible) | supprimer | *(supprimée)* | NIR — donnée très encadrée, aucun usage analytique |
| `date_naissance` | quasi_identifiant (indirect) | generaliser_age | `tranche_age` | L'âge exact n'est pas nécessaire, la tranche suffit à segmenter |
| `code_postal` | quasi_identifiant (indirect) | generaliser_code_postal | `departement` | Analyse territoriale au niveau du département |
| `sexe` | quasi_identifiant (indirect) | conserver | `sexe` | Analyse des écarts de satisfaction (quasi-identifiant, contrôlé par k-anonymat) |
| `canal` | — | conserver | `canal` | Donnée non personnelle |
| `motif` | — | conserver | `motif` | Donnée non personnelle |
| `montant_litige` | — | conserver | `montant_litige` | Donnée non personnelle |
| `statut` | — | conserver | `statut` | Donnée non personnelle |
| `delai_traitement_j` | — | conserver | `delai_traitement_j` | Donnée non personnelle |
| `commentaire` | email (direct) | caviarder_texte | `commentaire` | Texte libre utile à l'analyse des motifs, mais contenant parfois des coordonnées |

## 3. Risque de ré-identification (k-anonymat)

Quasi-identifiants : `tranche_age`, `departement`, `sexe` — objectif **k ≥ 5**

| | k obtenu | Classes à risque | Personnes à risque | Conforme |
|---|---|---|---|---|
| Après généralisation | 1 | 12 | 27 | ❌ |
| Après suppression des classes rares | 5 | 0 | 0 | ✅ |

## 4. Volumétrie et traçabilité

- Lignes en entrée : **3000**
- Lignes en sortie : **2973** (27 supprimées pour garantir le k-anonymat)
- Colonnes en entrée / sortie : 18 / 12
- Empreinte SHA-256 du fichier produit : `d72bb1d03b14b21db0715bf45bcafb23f9ae0f295b17ff99b79ef2732b1f08b2`

## 5. Rappels

- Les données en sortie sont **pseudonymisées**, pas anonymisées : elles restent des données
  personnelles au sens du RGPD et doivent être protégées comme telles.
- La clé de pseudonymisation est conservée hors du dépôt de code, par le responsable du traitement.
