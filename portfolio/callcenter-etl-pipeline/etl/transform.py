"""
Transformation : nettoyage, standardisation, contrôle et modélisation en étoile.

Principe : aucune ligne n'est supprimée silencieusement. Toute ligne écartée
est envoyée dans une table de rejets avec son motif, pour pouvoir être
analysée et corrigée à la source.
"""
from __future__ import annotations

import unicodedata

import pandas as pd

FORMATS_DATE = ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M:%S"]

MAPPING_CANAL = {"telephone": "Téléphone", "tel": "Téléphone",
                 "chat": "Chat",
                 "email": "Email", "e-mail": "Email", "mail": "Email"}
MAPPING_STATUT = {"decroche": "Décroché", "abandonne": "Abandonné", "abandon": "Abandonné"}
MAPPING_BOOLEEN = {"oui": True, "1": True, "true": True, "non": False, "0": False, "false": False}


# --------------------------------------------------------------------------- utilitaires
def normaliser_texte(valeur: str) -> str:
    """'  Téléphone ' -> 'telephone' (minuscules, sans accents, sans espaces superflus)."""
    sans_accents = unicodedata.normalize("NFKD", str(valeur)).encode("ascii", "ignore").decode()
    return sans_accents.strip().lower()


def parser_dates(serie: pd.Series) -> pd.Series:
    """Essaie chaque format connu ; les valeurs non reconnues deviennent NaT."""
    resultat = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")
    for fmt in FORMATS_DATE:
        essai = pd.to_datetime(serie, format=fmt, errors="coerce")
        resultat = resultat.fillna(essai)
    return resultat


def _rejeter(df: pd.DataFrame, masque: pd.Series, motif: str, source: str) -> pd.DataFrame:
    rejets = df.loc[masque.reindex(df.index, fill_value=False)]
    lignes_brutes = [" | ".join(map(str, valeurs)) for valeurs in rejets.itertuples(index=False)]
    return pd.DataFrame({
        "source": source,
        "cle": [str(v) for v in rejets.iloc[:, 0]],
        "motif": motif,
        "ligne_brute": lignes_brutes,
    }, columns=["source", "cle", "motif", "ligne_brute"])


# --------------------------------------------------------------------------- appels
def nettoyer_appels(appels: pd.DataFrame, agents_connus: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = appels.copy()
    rejets = []

    # 1. Doublons exacts sur la clé métier
    doublon = df.duplicated(subset="appel_id", keep="first")
    rejets.append(_rejeter(df, doublon, "doublon appel_id", "appels"))
    df = df[~doublon]

    # 2. Standardisation des libellés
    df["canal"] = df["canal"].map(normaliser_texte).map(MAPPING_CANAL)
    df["statut"] = df["statut"].map(normaliser_texte).map(MAPPING_STATUT)
    df["resolu_1er_contact"] = df["resolu_1er_contact"].map(normaliser_texte).map(MAPPING_BOOLEEN)

    # 3. Typage
    df["date_heure"] = parser_dates(df["date_heure"])
    df["duree_attente_s"] = pd.to_numeric(df["duree_attente_s"], errors="coerce")
    df["duree_traitement_s"] = pd.to_numeric(df["duree_traitement_s"], errors="coerce")
    df["agent_id"] = df["agent_id"].replace("", pd.NA)

    # 4. Règles de rejet (une ligne = un seul motif, le premier rencontré)
    regles = [
        ("date illisible", df["date_heure"].isna()),
        ("canal inconnu", df["canal"].isna()),
        ("statut inconnu", df["statut"].isna()),
        ("durée de traitement négative", df["duree_traitement_s"] < 0),
        ("agent absent du référentiel", df["agent_id"].notna() & ~df["agent_id"].isin(agents_connus)),
        ("appel décroché sans agent", (df["statut"] == "Décroché") & df["agent_id"].isna()),
    ]
    for motif, masque in regles:
        rejets.append(_rejeter(df, masque, motif, "appels"))
        df = df[~masque.reindex(df.index, fill_value=False)]

    return df.reset_index(drop=True), pd.concat(rejets, ignore_index=True)


# --------------------------------------------------------------------------- enquêtes
def nettoyer_enquetes(enquetes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = enquetes.copy()
    df["note_csat"] = pd.to_numeric(df["note_csat"], errors="coerce")
    hors_echelle = ~df["note_csat"].between(1, 5)
    rejets = _rejeter(enquetes, hors_echelle, "note CSAT hors échelle 1-5", "enquetes")
    df = df[~hors_echelle].drop_duplicates("appel_id")
    df["note_csat"] = df["note_csat"].astype(int)
    return df.reset_index(drop=True), rejets


# --------------------------------------------------------------------------- modèle en étoile
def construire_dim_date(dates: pd.Series) -> pd.DataFrame:
    jours = pd.date_range(dates.min().normalize(), dates.max().normalize(), freq="D")
    noms_jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    return pd.DataFrame({
        "date_key": jours.strftime("%Y%m%d").astype(int),
        "date": jours.date,
        "annee": jours.year,
        "trimestre": jours.quarter,
        "mois": jours.month,
        "semaine_iso": jours.isocalendar().week.astype(int).values,
        "jour_semaine": [noms_jours[d] for d in jours.weekday],
        "est_weekend": jours.weekday >= 5,
    })


def construire_dim_agent(agents: pd.DataFrame) -> pd.DataFrame:
    dim = agents.copy()
    # Minimisation RGPD : l'entrepôt analytique n'a pas besoin du nom complet
    dim["agent_libelle"] = dim["prenom"] + " " + dim["nom"].str[0] + "."
    dim["date_embauche"] = pd.to_datetime(dim["date_embauche"]).dt.date
    return dim[["agent_id", "agent_libelle", "site", "equipe", "date_embauche"]]


def construire_dim_campagne(campagnes: pd.DataFrame) -> pd.DataFrame:
    dim = campagnes.copy()
    dim["date_debut"] = pd.to_datetime(dim["date_debut"]).dt.date
    return dim[["campagne_id", "client", "secteur", "objectif_csat", "date_debut"]]


def construire_fait_interactions(appels: pd.DataFrame, enquetes: pd.DataFrame) -> pd.DataFrame:
    fait = appels.merge(enquetes, on="appel_id", how="left")
    return pd.DataFrame({
        "appel_id": fait["appel_id"],
        "date_key": fait["date_heure"].dt.strftime("%Y%m%d").astype(int),
        "heure": fait["date_heure"].dt.hour,
        "date_heure": fait["date_heure"],
        "agent_id": fait["agent_id"],
        "campagne_id": fait["campagne_id"],
        "canal": fait["canal"],
        "statut": fait["statut"],
        "duree_attente_s": fait["duree_attente_s"],
        "duree_traitement_s": fait["duree_traitement_s"],
        "resolu_1er_contact": fait["resolu_1er_contact"],
        "note_csat": fait["note_csat"].astype("Int64"),
        # numero_client volontairement NON chargé : donnée personnelle inutile à l'analyse
    })


def transformer(sources: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    agents_connus = set(sources["agents"]["agent_id"])
    appels, rejets_appels = nettoyer_appels(sources["appels"], agents_connus)
    enquetes, rejets_enquetes = nettoyer_enquetes(sources["enquetes"])

    tables = {
        "dim_date": construire_dim_date(appels["date_heure"]),
        "dim_agent": construire_dim_agent(sources["agents"]),
        "dim_campagne": construire_dim_campagne(sources["campagnes"]),
        "fait_interactions": construire_fait_interactions(appels, enquetes),
    }
    return tables, pd.concat([rejets_appels, rejets_enquetes], ignore_index=True)
