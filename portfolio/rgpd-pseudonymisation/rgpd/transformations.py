"""
Techniques de protection applicables colonne par colonne.

Rappel RGPD (considérant 26) :
  - une donnée PSEUDONYMISÉE reste une donnée personnelle (ré-identification possible avec la clé) ;
  - une donnée ANONYMISÉE ne l'est plus (ré-identification impossible, irréversible).
Ce module fait surtout de la pseudonymisation + de la minimisation ; la vérification du
k-anonymat (k_anonymat.py) mesure le risque de ré-identification résiduel.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from datetime import date

import pandas as pd

from rgpd.detection import caviarder_texte


def _cle_secrete() -> bytes:
    cle = os.environ.get("RGPD_CLE_PSEUDO")
    if not cle:
        raise RuntimeError(
            "Variable d'environnement RGPD_CLE_PSEUDO absente : la clé de pseudonymisation "
            "ne doit jamais être écrite dans le code ni dans le dépôt Git."
        )
    return cle.encode()


def pseudonymiser(serie: pd.Series, prefixe: str = "ID") -> pd.Series:
    """HMAC-SHA256 avec clé secrète : même valeur d'entrée -> même pseudonyme (les jointures restent
    possibles entre fichiers), mais impossible de retrouver la valeur sans la clé.
    Un simple SHA-256 sans clé serait cassable : on peut hacher tous les numéros de téléphone possibles."""
    cle = _cle_secrete()

    def jeton(valeur):
        if pd.isna(valeur) or str(valeur).strip() == "":
            return None
        empreinte = hmac.new(cle, str(valeur).strip().lower().encode(), hashlib.sha256).hexdigest()
        return f"{prefixe}_{empreinte[:16]}"

    return serie.map(jeton)


def masquer_email(serie: pd.Series) -> pd.Series:
    """jean.dupont@mail.fr -> j*********@mail.fr (utile pour un affichage opérationnel)."""
    def masque(v):
        if not isinstance(v, str) or "@" not in v:
            return v
        local, domaine = v.split("@", 1)
        return f"{local[0]}{'*' * max(len(local) - 1, 3)}@{domaine}"
    return serie.map(masque)


def masquer_telephone(serie: pd.Series) -> pd.Series:
    """06 12 34 56 78 -> 06******78."""
    def masque(v):
        chiffres = "".join(c for c in str(v) if c.isdigit())
        return f"{chiffres[:2]}{'*' * 6}{chiffres[-2:]}" if len(chiffres) >= 10 else None
    return serie.map(masque)


def generaliser_age(serie: pd.Series, reference: date | None = None, pas: int = 10) -> pd.Series:
    """Date de naissance -> tranche d'âge (ex. « 30-39 »). L'âge exact n'est presque jamais nécessaire."""
    reference = pd.Timestamp(reference or date.today())
    naissance = pd.to_datetime(serie, errors="coerce")
    age = ((reference - naissance).dt.days // 365.25)

    def tranche(a):
        if pd.isna(a):
            return None
        bas = int(a // pas * pas)
        return f"{bas}-{bas + pas - 1}"
    return age.map(tranche)


def generaliser_code_postal(serie: pd.Series) -> pd.Series:
    """86000 -> 86 (département) ; 97400 -> 974 (outre-mer : code à 3 chiffres)."""
    cp = serie.astype(str).str.zfill(5)
    outre_mer = cp.str.startswith(("97", "98"))
    return cp.str[:2].mask(outre_mer, cp.str[:3])


def caviarder(serie: pd.Series) -> pd.Series:
    return serie.map(caviarder_texte)


STRATEGIES = {
    "pseudonymiser": pseudonymiser,
    "masquer_email": masquer_email,
    "masquer_telephone": masquer_telephone,
    "generaliser_age": generaliser_age,
    "generaliser_code_postal": generaliser_code_postal,
    "caviarder_texte": caviarder,
}


def appliquer_politique(df: pd.DataFrame, politique: dict[str, dict]) -> pd.DataFrame:
    """Applique la stratégie définie pour chaque colonne. Une colonne absente de la politique
    est SUPPRIMÉE par défaut : on ne transmet que ce qui a été explicitement autorisé."""
    sortie = pd.DataFrame(index=df.index)
    for colonne, regle in politique.items():
        strategie = regle["strategie"]
        if strategie == "supprimer":
            continue
        cible = regle.get("renommer_en", colonne)
        if strategie == "conserver":
            sortie[cible] = df[colonne]
        else:
            params = {k: v for k, v in regle.items() if k not in ("strategie", "renommer_en", "justification")}
            sortie[cible] = STRATEGIES[strategie](df[colonne], **params)
    return sortie
