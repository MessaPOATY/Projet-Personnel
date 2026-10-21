"""
Mesure du risque de ré-identification par le k-anonymat.

Un jeu de données est k-anonyme si chaque combinaison de quasi-identifiants
(ex. tranche d'âge + département + sexe) est partagée par AU MOINS k personnes.
Si une combinaison est unique (k = 1), la personne peut être ré-identifiée
en croisant avec une autre source, même sans nom ni email.
"""
from __future__ import annotations

import pandas as pd


def tailles_classes(df: pd.DataFrame, quasi_identifiants: list[str]) -> pd.DataFrame:
    return (df.groupby(quasi_identifiants, dropna=False).size()
              .rename("effectif").reset_index().sort_values("effectif"))


def evaluer(df: pd.DataFrame, quasi_identifiants: list[str], k_cible: int) -> dict:
    classes = tailles_classes(df, quasi_identifiants)
    a_risque = classes[classes["effectif"] < k_cible]
    return {
        "quasi_identifiants": quasi_identifiants,
        "k_cible": k_cible,
        "k_obtenu": int(classes["effectif"].min()),
        "nb_classes": len(classes),
        "classes_a_risque": len(a_risque),
        "personnes_a_risque": int(a_risque["effectif"].sum()),
        "conforme": bool(classes["effectif"].min() >= k_cible),
    }


def supprimer_classes_rares(df: pd.DataFrame, quasi_identifiants: list[str], k_cible: int) -> pd.DataFrame:
    """Suppression des lignes appartenant à une classe trop petite (technique de « suppression locale »).
    Alternative : généraliser davantage (tranches d'âge plus larges, région au lieu du département)."""
    effectifs = df.groupby(quasi_identifiants, dropna=False)[quasi_identifiants[0]].transform("size")
    return df[effectifs >= k_cible].copy()
