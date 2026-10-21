"""
Catalogue des règles de contrôle qualité.

Chaque règle est une fonction qui reçoit un DataFrame (et ses paramètres) et
renvoie une Series booléenne : True = ligne EN ERREUR.
Ajouter une règle = écrire une fonction + l'enregistrer avec @regle("nom").
"""
from __future__ import annotations

from typing import Callable

import pandas as pd

CATALOGUE: dict[str, Callable[..., pd.Series]] = {}


def regle(nom: str):
    def decorateur(fonction):
        CATALOGUE[nom] = fonction
        return fonction
    return decorateur


def _vide(serie: pd.Series) -> pd.Series:
    return serie.isna() | serie.astype(str).str.strip().eq("")


@regle("non_null")
def non_null(df: pd.DataFrame, colonne: str, **_) -> pd.Series:
    """Complétude : la valeur doit être renseignée."""
    return _vide(df[colonne])


@regle("unique")
def unique(df: pd.DataFrame, colonnes: list[str] | str, **_) -> pd.Series:
    """Unicité : la (combinaison de) colonne(s) ne doit pas apparaître deux fois."""
    colonnes = [colonnes] if isinstance(colonnes, str) else colonnes
    return df.duplicated(subset=colonnes, keep=False)


@regle("valeurs_autorisees")
def valeurs_autorisees(df: pd.DataFrame, colonne: str, valeurs: list, **_) -> pd.Series:
    """Validité : la valeur doit appartenir à une liste fermée (valeurs vides ignorées)."""
    return ~_vide(df[colonne]) & ~df[colonne].isin(valeurs)


@regle("intervalle")
def intervalle(df: pd.DataFrame, colonne: str, min=None, max=None, **_) -> pd.Series:
    """Validité : valeur numérique comprise dans [min, max]. Non numérique = erreur."""
    valeurs = pd.to_numeric(df[colonne], errors="coerce")
    erreur = valeurs.isna() & ~_vide(df[colonne])
    if min is not None:
        erreur |= valeurs < min
    if max is not None:
        erreur |= valeurs > max
    return erreur


@regle("format")
def format_regex(df: pd.DataFrame, colonne: str, motif: str, **_) -> pd.Series:
    """Validité : la valeur respecte une expression régulière (email, code postal…)."""
    renseigne = ~_vide(df[colonne])
    return renseigne & ~df[colonne].astype(str).str.fullmatch(motif)


@regle("date_valide")
def date_valide(df: pd.DataFrame, colonne: str, format: str = "%Y-%m-%d", pas_dans_le_futur: bool = True,
                **_) -> pd.Series:
    """Validité / exactitude : date lisible et, optionnellement, pas dans le futur."""
    dates = pd.to_datetime(df[colonne], format=format, errors="coerce")
    erreur = dates.isna() & ~_vide(df[colonne])
    if pas_dans_le_futur:
        erreur |= dates > pd.Timestamp.today()
    return erreur


@regle("ordre_dates")
def ordre_dates(df: pd.DataFrame, avant: str, apres: str, format: str = "%Y-%m-%d", **_) -> pd.Series:
    """Cohérence : `avant` doit précéder `apres` (ex. date d'entrée < date de sortie)."""
    d1 = pd.to_datetime(df[avant], format=format, errors="coerce")
    d2 = pd.to_datetime(df[apres], format=format, errors="coerce")
    return d1.notna() & d2.notna() & (d1 > d2)


@regle("cle_etrangere")
def cle_etrangere(df: pd.DataFrame, colonne: str, reference: pd.DataFrame, colonne_reference: str,
                  **_) -> pd.Series:
    """Cohérence : la valeur doit exister dans un référentiel (intégrité référentielle)."""
    return ~_vide(df[colonne]) & ~df[colonne].isin(reference[colonne_reference])


@regle("expression")
def expression(df: pd.DataFrame, condition: str, **_) -> pd.Series:
    """Règle métier libre, écrite comme une condition pandas qui doit être VRAIE.
    Exemple : "salaire_brut_annuel >= 21000 or temps_travail < 1"."""
    return ~df.eval(condition).fillna(False).astype(bool)
