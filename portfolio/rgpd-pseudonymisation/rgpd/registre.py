"""Génère la fiche de traitement (documentation du traitement, au format Markdown)."""
from __future__ import annotations

from datetime import datetime

from rgpd.detection import Detection


def generer_fiche(config: dict, detections: list[Detection], k_avant: dict, k_apres: dict,
                  volumes: dict, empreinte_sortie: str) -> str:
    t = config["traitement"]
    par_colonne = {d.colonne: d for d in detections}

    lignes_colonnes = []
    for colonne, regle in config["colonnes"].items():
        d = par_colonne.get(colonne)
        categorie = f"{d.categorie} ({d.niveau})" if d else "—"
        sortie = "*(supprimée)*" if regle["strategie"] == "supprimer" else f"`{regle.get('renommer_en', colonne)}`"
        lignes_colonnes.append(
            f"| `{colonne}` | {categorie} | {regle['strategie']} | {sortie} | {regle.get('justification', '')} |"
        )

    return f"""# Fiche de traitement — {t['nom']}

*Générée automatiquement le {datetime.now():%d/%m/%Y à %H:%M}*

## 1. Description du traitement

| | |
|---|---|
| **Finalité** | {t['finalite'].strip()} |
| **Base légale** | {t['base_legale']} |
| **Responsable** | {t['responsable']} |
| **Destinataires** | {t['destinataires']} |
| **Durée de conservation** | {t['duree_conservation']} |

## 2. Données traitées et mesures appliquées

| Colonne source | DCP détectée | Mesure | Colonne en sortie | Justification |
|---|---|---|---|---|
{chr(10).join(lignes_colonnes)}

## 3. Risque de ré-identification (k-anonymat)

Quasi-identifiants : {', '.join(f'`{q}`' for q in k_apres['quasi_identifiants'])} — objectif **k ≥ {k_apres['k_cible']}**

| | k obtenu | Classes à risque | Personnes à risque | Conforme |
|---|---|---|---|---|
| Après généralisation | {k_avant['k_obtenu']} | {k_avant['classes_a_risque']} | {k_avant['personnes_a_risque']} | {'✅' if k_avant['conforme'] else '❌'} |
| Après suppression des classes rares | {k_apres['k_obtenu']} | {k_apres['classes_a_risque']} | {k_apres['personnes_a_risque']} | {'✅' if k_apres['conforme'] else '❌'} |

## 4. Volumétrie et traçabilité

- Lignes en entrée : **{volumes['entree']}**
- Lignes en sortie : **{volumes['sortie']}** ({volumes['entree'] - volumes['sortie']} supprimées pour garantir le k-anonymat)
- Colonnes en entrée / sortie : {volumes['colonnes_entree']} / {volumes['colonnes_sortie']}
- Empreinte SHA-256 du fichier produit : `{empreinte_sortie}`

## 5. Rappels

- Les données en sortie sont **pseudonymisées**, pas anonymisées : elles restent des données
  personnelles au sens du RGPD et doivent être protégées comme telles.
- La clé de pseudonymisation est conservée hors du dépôt de code, par le responsable du traitement.
"""
