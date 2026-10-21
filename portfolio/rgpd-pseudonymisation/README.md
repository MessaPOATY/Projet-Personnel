# 🔐 Pseudonymisation RGPD d'exports de données

![CI](https://github.com/GITHUB_USER/rgpd-pseudonymisation/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![RGPD](https://img.shields.io/badge/RGPD-privacy%20by%20design-purple)

Outil Python qui prépare un export contenant des **données personnelles** pour un usage
analytique, **en appliquant le RGPD dès la conception** :

1. **détecte** automatiquement les données personnelles (par nom de colonne *et* par contenu) ;
2. applique une **politique de protection** décrite en YAML (supprimer, pseudonymiser, généraliser, caviarder) ;
3. **vérifie qu'aucune donnée personnelle ne fuit** dans le fichier produit ;
4. mesure le **risque de ré-identification** (k-anonymat) et le corrige ;
5. génère automatiquement la **fiche de traitement** qui documente tout ce qui a été fait.

> ℹ️ Projet personnel. Démonstration sur 3 000 réclamations clients **entièrement fictives**
> (noms, emails, téléphones, IBAN et n° de sécurité sociale générés aléatoirement).

---

## 🎯 Pourquoi ce projet

Une équipe Data a souvent besoin d'analyser des données qui contiennent des informations
personnelles, alors qu'elle n'a besoin **d'aucune** d'entre elles pour répondre à sa question.
Le RGPD impose la **minimisation** (art. 5) et la **protection des données dès la conception** (art. 25).

Ce projet transforme ces principes en **contrôles automatiques** plutôt qu'en bonnes intentions.

## 🔄 Avant / après

**Avant** (extrait brut) :

| client_id | nom | email | telephone | date_naissance | code_postal | commentaire |
|---|---|---|---|---|---|---|
| C02084 | Simon | ines.simon148@exemple-mail.fr | 07 60 71 02 48 | 1974-12-09 | 86100 | Remboursement à effectuer sur le compte FR76 4014 9282… |

**Après** :

| client_pseudo | tranche_age | departement | commentaire |
|---|---|---|---|
| CLI_b45829698440cd56 | 50-59 | 86 | Remboursement à effectuer sur le compte [IBAN]. |

Les colonnes `nom`, `prenom`, `email`, `telephone`, `iban_remboursement`, `numero_secu` sont supprimées ;
les analyses par motif, canal, délai, tranche d'âge ou département restent possibles.

## 🧰 Techniques de protection

| Technique | Exemple | Quand l'utiliser |
|---|---|---|
| **Suppression** | `email` → *(supprimée)* | La donnée n'est pas utile à la finalité |
| **Pseudonymisation** (HMAC-SHA256 + clé secrète) | `C02084` → `CLI_b458…` | Il faut pouvoir relier les lignes d'une même personne (jointures, comptages) |
| **Généralisation** | `1974-12-09` → `50-59` ; `86100` → `86` | La précision n'est pas nécessaire |
| **Caviardage** de texte libre | `…au 06 12 34 56 78` → `…au [TELEPHONE]` | Champs commentaires |
| **Masquage** | `06 12 34 56 78` → `06******78` | Affichage opérationnel (disponible, non utilisé dans la démo) |

**Pourquoi HMAC et pas un simple hash ?** Un SHA-256 sans clé d'un numéro de client ou de
téléphone se « casse » facilement en hachant toutes les valeurs possibles. Avec une clé secrète
(stockée en variable d'environnement, **jamais dans le code**), c'est impossible sans la clé.

## 🛡️ Garde-fous automatiques

- **Liste blanche** : toute colonne absente de la politique est supprimée par défaut.
- **Politique incomplète = arrêt** : si une donnée personnelle est détectée sans règle associée, le traitement s'arrête.
- **Contrôle de fuite** : le fichier produit est re-scanné ; s'il contient encore un email, un téléphone, un IBAN ou un NIR, rien n'est exporté.
- **k-anonymat** : chaque combinaison (tranche d'âge × département × sexe) doit concerner au moins 5 personnes.
  Dans la démo, 27 personnes étaient ré-identifiables (ex. une seule femme de 50-59 ans à La Réunion) : elles sont retirées.

```
1. 11 colonne(s) contenant des données personnelles détectée(s) :
   - email                email              [direct]    via nom + contenu
   - iban_remboursement   iban               [sensible]  via nom + contenu
   - commentaire          email              [direct]    via contenu      ← détecté malgré un nom anodin
   ...
2. Politique appliquée : 18 -> 12 colonnes
3. Contrôle de fuite : aucune DCP directe résiduelle ✔
4. k-anonymat : k = 1 -> 5 (27 ligne(s) à risque retirée(s))
5. Export : sortie/reclamations_pseudonymise.csv
```

📄 Exemple de fiche de traitement générée : [`docs/exemple_fiche_traitement.md`](docs/exemple_fiche_traitement.md)

## 🚀 Lancer le projet

```bash
pip install -r requirements.txt
python scripts/generate_data.py

export RGPD_CLE_PSEUDO="une-cle-longue-et-aleatoire"     # Windows : set RGPD_CLE_PSEUDO=...
python -m rgpd.cli --entree data/reclamations_brut.csv --politique config/politique_reclamations.yaml
pytest     # 13 tests
```

## 📁 Structure

```
rgpd/
├── detection.py        # détection des DCP (nom de colonne + expressions régulières)
├── transformations.py  # pseudonymisation, masquage, généralisation, caviardage
├── k_anonymat.py       # mesure et correction du risque de ré-identification
├── registre.py         # génération de la fiche de traitement
└── cli.py              # enchaînement des étapes et garde-fous
config/politique_reclamations.yaml
```

## ⚠️ Limites (et ce que j'en retiens)

- Des données **pseudonymisées restent des données personnelles** : elles doivent toujours être protégées.
- La détection par expressions régulières ne trouve pas tout (ex. un nom de famille dans un commentaire).
  Une étape de **reconnaissance d'entités nommées** (NER, ex. spaCy) serait une amélioration naturelle.
- Le k-anonymat ne protège pas contre toutes les attaques (cf. l-diversité, confidentialité différentielle).
- Ce projet est un exercice technique : il ne remplace pas l'avis d'un **DPO**.

## 🧠 Compétences mobilisées

`RGPD` `gouvernance des données` `Python` `pandas` `cryptographie (HMAC)` `expressions régulières`
`k-anonymat` `documentation` `tests unitaires` `CI/CD`
