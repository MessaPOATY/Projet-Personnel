"""
Détection automatique des données personnelles (DCP) dans un jeu de données.

Deux signaux combinés :
  1. le NOM de la colonne (ex. « email », « tel », « nom »)
  2. le CONTENU : part des valeurs qui correspondent à un motif (email, téléphone, IBAN, n° de sécu…)
Le résultat est une PROPOSITION : un humain valide la politique finale (config YAML).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

# L'ordre compte pour le caviardage : IBAN et NIR avant le téléphone,
# sinon une suite de chiffres d'IBAN pourrait être prise pour un numéro.
MOTIFS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "iban": re.compile(r"\bFR\d{2}(?:\s?\d{4}){5}\s?\d{3}\b"),
    "nir": re.compile(r"\b[12]\s?\d{2}\s?(?:0[1-9]|1[0-2])\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b"),
    "telephone": re.compile(r"(?:\+33\s?|\b0)[1-9](?:[\s.-]?\d{2}){4}\b"),
}

INDICES_NOMS = {
    "identifiant_direct": ["nom", "prenom", "name", "adresse", "address"],
    "email": ["mail", "courriel"],
    "telephone": ["tel", "phone", "mobile", "portable"],
    "iban": ["iban", "rib"],
    "nir": ["nir", "secu", "securite_sociale"],
    "identifiant_indirect": ["client_id", "id_client", "matricule", "num_client"],
    "quasi_identifiant": ["naissance", "birth", "age", "code_postal", "cp", "ville", "sexe", "genre"],
}


@dataclass
class Detection:
    colonne: str
    categorie: str
    signal: str            # "nom de colonne", "contenu" ou "nom + contenu"
    taux_correspondance: float

    @property
    def niveau(self) -> str:
        if self.categorie in ("iban", "nir"):
            return "sensible"           # risque élevé en cas de fuite
        if self.categorie in ("quasi_identifiant", "identifiant_indirect"):
            return "indirect"           # ré-identifiant en combinaison
        return "direct"


def _categorie_par_nom(colonne: str) -> str | None:
    nom = colonne.lower()
    for categorie, indices in INDICES_NOMS.items():
        if any(indice in nom for indice in indices):
            return categorie
    return None


def _categorie_par_contenu(serie: pd.Series, seuil: float) -> tuple[str | None, float]:
    valeurs = serie.dropna().astype(str)
    if valeurs.empty:
        return None, 0.0
    echantillon = valeurs.sample(min(len(valeurs), 500), random_state=0)
    meilleur, meilleur_taux = None, 0.0
    for categorie, motif in MOTIFS.items():
        taux = echantillon.str.contains(motif).mean()
        if taux > meilleur_taux:
            meilleur, meilleur_taux = categorie, float(taux)
    return (meilleur, meilleur_taux) if meilleur_taux >= seuil else (None, meilleur_taux)


def detecter(df: pd.DataFrame, seuil_contenu: float = 0.05) -> list[Detection]:
    """Le seuil est bas exprès : une colonne de texte libre (commentaire) qui contient
    QUELQUES emails doit être signalée, même si la majorité des valeurs est anodine."""
    detections = []
    for colonne in df.columns:
        par_nom = _categorie_par_nom(colonne)
        par_contenu, taux = _categorie_par_contenu(df[colonne], seuil_contenu)
        if par_nom and par_contenu:
            detections.append(Detection(colonne, par_contenu, "nom + contenu", taux))
        elif par_contenu:
            detections.append(Detection(colonne, par_contenu, "contenu", taux))
        elif par_nom:
            detections.append(Detection(colonne, par_nom, "nom de colonne", taux))
    return detections


def caviarder_texte(texte: str) -> str:
    """Remplace les DCP trouvées dans un texte libre par une étiquette."""
    if not isinstance(texte, str):
        return texte
    for categorie, motif in MOTIFS.items():
        texte = motif.sub(f"[{categorie.upper()}]", texte)
    return texte
