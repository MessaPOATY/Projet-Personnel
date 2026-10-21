# Guide — mettre ton portfolio en ligne et le défendre en entretien

## 1. Mettre en ligne (≈ 10 minutes)

**Option A — automatique (recommandée)**

1. Installe **Git** (https://git-scm.com) et **GitHub CLI** (https://cli.github.com).
2. Ouvre un terminal (sous Windows : *Git Bash*) dans ce dossier `portfolio/`.
3. Connecte-toi une fois : `gh auth login` (choisis GitHub.com → HTTPS → navigateur),
   puis indique ton identité Git (elle signe tes commits) :
   `git config --global user.name "Mesanibaumh POATY"` et `git config --global user.email "messapoaty46@gmail.com"`
4. Lance : `bash publier.sh`

Le script remplace `GITHUB_USER` par ton pseudo dans tous les liens, crée les 6 dépôts publics et les envoie.

**Option B — à la main avec GitHub Desktop**

1. Dans chaque README, remplace `GITHUB_USER` par ton pseudo GitHub (et `LIEN_LINKEDIN` dans le README de profil).
2. Renomme le dossier `GITHUB_USER` avec **exactement** ton pseudo : c'est le dépôt spécial qui s'affiche sur ta page de profil.
3. Dans GitHub Desktop : *File → Add local repository* pour chaque dossier, puis *Publish repository* (décoche « Keep this code private »).

⚠️ Évite l'upload par glisser-déposer sur github.com : le dossier caché `.github/` (l'intégration continue) est souvent oublié.

## 2. Après la mise en ligne

- **Épingle** les 5 projets sur ton profil : *Customize your pins*.
- Sur chaque dépôt, onglet **Actions** : vérifie que la coche est verte ✅.
- Ajoute des **topics** à chaque dépôt (roue dentée « About ») : `data-engineering`, `python`, `sql`, `etl`, `data-quality`, `rgpd`…
- Optionnel : déploie le dashboard gratuitement sur **Streamlit Community Cloud** (share.streamlit.io → connecte le dépôt → `app.py`) et ajoute le lien en haut de son README.
- Mets le lien `github.com/<ton-pseudo>` sur ton CV (à la place de « Portfolio ») et dans ta candidature Konecta.

## 3. Avant l'entretien : maîtrise chaque projet

Le recruteur va ouvrir le code et te poser des questions. **Lance chaque projet sur ton ordinateur**,
lis le code fichier par fichier et modifie-le (change un seuil, ajoute une règle) pour te l'approprier.
Les données sont synthétiques et c'est écrit dans chaque README : dis-le simplement si on te le demande.

Questions probables et pistes de réponse :

| Projet | Question | Ce qu'il faut savoir expliquer |
|---|---|---|
| ETL | Pourquoi un modèle en étoile ? | Faits = événements mesurables, dimensions = axes d'analyse ; requêtes simples et rapides pour Power BI |
| ETL | Que se passe-t-il si les données sources sont très mauvaises ? | Porte qualité : au-delà de 5 % de rejets, rien n'est chargé, l'échec est journalisé |
| ETL | Pourquoi ne pas supprimer directement les lignes fausses ? | Traçabilité : la table `rejets` garde le motif pour corriger à la source |
| Qualité | Différence complétude / validité / cohérence ? | Renseignée ? / au bon format ? / cohérente avec les autres données ? |
| Qualité | Pourquoi des règles en YAML ? | Lisibles et modifiables par les métiers sans toucher au code |
| SQL | À quoi sert `LAG` / `RANK` / `QUALIFY` ? | Valeur de la ligne précédente / classement / filtrer sur une fonction de fenêtre |
| SQL | Pourquoi des couches staging / marts ? | Séparer nettoyage et logique métier ; chaque table a un rôle, plus facile à maintenir et tester |
| RGPD | Pseudonymisation vs anonymisation ? | Pseudonymisé = ré-identifiable avec la clé, reste une donnée personnelle ; anonymisé = irréversible |
| RGPD | Pourquoi HMAC plutôt que SHA-256 ? | Sans clé, on peut hacher toutes les valeurs possibles et retrouver l'original |
| RGPD | C'est quoi le k-anonymat ? | Chaque combinaison d'âge/département/sexe doit concerner au moins k personnes |
| Dashboard | Comment as-tu trouvé le goulot ? | Comparaison de la durée de chaque étape entre dossiers à l'heure et en retard |
| Dashboard | Lien avec ton stage ? | Même problématique (délais, retards, KPI logistiques), refaite en Python avec des données fictives |

## 4. Le lien avec l'offre Konecta

| Ce que demande l'offre | Où le montrer |
|---|---|
| Collecter, intégrer, transformer, contrôler des données de sources variées | Pipeline ETL |
| Automatisation et suivi des flux | ETL (journal d'exécution, CI) · Data Quality Checker (code retour) |
| Modélisation jusqu'à la mise à disposition | ETL (étoile) · SQL (staging → marts) |
| Valorisation pour le pilotage | SQL (KPI relation client) · Dashboard |
| Contrôles de qualité et fiabilité | Data Quality Checker · tests SQL |
| Documentation des données et des flux | Dictionnaire de données · fiche de traitement · README |
| Gouvernance, sécurité, RGPD | Pseudonymisation RGPD · minimisation dans l'ETL |
| SQL, Python, Power BI | Partout · vues prêtes pour Power BI |

Konecta est un groupe de **relation client** : les projets ETL et SQL utilisent justement
des indicateurs de centre de contact (taux d'abandon, DMT, FCR, CSAT, SLA). Cite-les en entretien.
