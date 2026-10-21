#!/usr/bin/env bash
# =====================================================================
# Publie les 5 projets + le README de profil sur ton compte GitHub.
# Prérequis : git et GitHub CLI (https://cli.github.com), puis une fois : gh auth login
# Utilisation (depuis ce dossier) :  bash publier.sh
# =====================================================================
set -euo pipefail

UTILISATEUR=$(gh api user --jq .login)
echo "Compte GitHub détecté : $UTILISATEUR"
read -r -p "Lien de ton profil LinkedIn (laisser vide pour plus tard) : " LINKEDIN

# Remplace les marqueurs dans tous les README
grep -rl "GITHUB_USER\|LIEN_LINKEDIN" --include=README.md . | while read -r f; do
  sed -i.bak "s#GITHUB_USER#${UTILISATEUR}#g; s#LIEN_LINKEDIN#${LINKEDIN:-https://www.linkedin.com}#g" "$f" && rm -f "$f.bak"
done
[ -d GITHUB_USER ] && mv GITHUB_USER "$UTILISATEUR"

declare -A DESCRIPTIONS=(
  [callcenter-etl-pipeline]="Pipeline ETL multi-sources (CSV, JSON, Excel) vers un entrepôt DuckDB en étoile, avec porte qualité, rejets tracés et CI"
  [data-quality-checker]="Contrôles qualité de données pilotés par règles YAML : score par dimension, rapport HTML, blocage automatique"
  [sql-kpi-relation-client]="Modélisation SQL en couches (staging/intermediate/marts), tests de données et analyses avec fonctions de fenêtre"
  [rgpd-pseudonymisation]="Détection de données personnelles, pseudonymisation HMAC, k-anonymat et fiche de traitement RGPD automatique"
  [dashboard-delais-livraison]="Tableau de bord Streamlit de pilotage des délais de livraison : KPI, goulot d'étranglement, Pareto des causes"
  [$UTILISATEUR]="Mon profil GitHub"
)

for depot in "${!DESCRIPTIONS[@]}"; do
  echo "──── $depot"
  (
    cd "$depot"
    [ -d .git ] || git init -q -b main
    git add -A
    git commit -q -m "Première version du projet" || true
    gh repo create "$depot" --public --description "${DESCRIPTIONS[$depot]}" --source . --push
  )
done

echo
echo "✅ Terminé : https://github.com/$UTILISATEUR"
echo "Pense à épingler les 5 projets sur ton profil (Customize your pins)."
