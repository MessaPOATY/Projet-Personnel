"""
Logique d'analyse, séparée de l'interface Streamlit : chaque fonction est testable
et réutilisable (notebook, rapport automatique, autre outil de visualisation).
"""
from __future__ import annotations

import pandas as pd

ETAPES = {
    "j_port": "Passage portuaire",
    "j_douane": "Dédouanement",
    "j_transport": "Transport final",
}


def charger(chemin) -> pd.DataFrame:
    dates = ["date_arrivee", "date_sortie_port", "date_dedouanement", "date_livraison_prevue", "date_livraison"]
    df = pd.read_csv(chemin, parse_dates=dates, keep_default_na=False)
    return preparer(df)


def preparer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["j_port"] = (df["date_sortie_port"] - df["date_arrivee"]).dt.days
    df["j_douane"] = (df["date_dedouanement"] - df["date_sortie_port"]).dt.days
    df["j_transport"] = (df["date_livraison"] - df["date_dedouanement"]).dt.days
    df["delai_total_j"] = (df["date_livraison"] - df["date_arrivee"]).dt.days
    df["retard_j"] = (df["date_livraison"] - df["date_livraison_prevue"]).dt.days.clip(lower=0)
    df["en_retard"] = df["retard_j"] > 0
    df["mois"] = df["date_arrivee"].dt.to_period("M").dt.to_timestamp()
    df["cause_retard_declaree"] = df["cause_retard_declaree"].replace("", "Non renseignée")
    return df


def indicateurs(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"dossiers": 0, "delai_moyen": 0.0, "delai_median": 0.0, "taux_retard": 0.0, "retard_moyen": 0.0}
    retards = df.loc[df["en_retard"], "retard_j"]
    return {
        "dossiers": len(df),
        "delai_moyen": round(float(df["delai_total_j"].mean()), 1),
        "delai_median": float(df["delai_total_j"].median()),
        "taux_retard": round(100 * float(df["en_retard"].mean()), 1),
        "retard_moyen": round(float(retards.mean()), 1) if len(retards) else 0.0,
    }


def decomposition_etapes(df: pd.DataFrame) -> pd.DataFrame:
    """Durée moyenne de chaque étape, pour les dossiers à l'heure et en retard :
    l'étape où l'écart est le plus grand est le goulot d'étranglement."""
    res = (df.assign(statut=df["en_retard"].map({True: "En retard", False: "À l'heure"}))
             .groupby("statut")[list(ETAPES)].mean().round(1)
             .rename(columns=ETAPES).T)
    if {"En retard", "À l'heure"} <= set(res.columns):
        res["Écart (j)"] = (res["En retard"] - res["À l'heure"]).round(1)
    return res


def pareto_causes(df: pd.DataFrame) -> pd.DataFrame:
    """Causes des retards, triées, avec pourcentage cumulé (règle des 80/20)."""
    retards = df[df["en_retard"]]
    p = (retards.groupby("cause_retard_declaree")
                .agg(dossiers=("dossier_id", "count"), jours_perdus=("retard_j", "sum"))
                .sort_values("jours_perdus", ascending=False))
    p["part_jours_pct"] = (100 * p["jours_perdus"] / p["jours_perdus"].sum()).round(1)
    p["cumul_pct"] = p["part_jours_pct"].cumsum().round(1)
    return p.reset_index().rename(columns={"cause_retard_declaree": "cause"})


def evolution_mensuelle(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("mois")
              .agg(dossiers=("dossier_id", "count"),
                   delai_moyen=("delai_total_j", "mean"),
                   taux_retard=("en_retard", "mean"))
              .assign(taux_retard=lambda x: (100 * x["taux_retard"]).round(1),
                      delai_moyen=lambda x: x["delai_moyen"].round(1))
              .reset_index())


def comparatif(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    return (df.groupby(dimension)
              .agg(dossiers=("dossier_id", "count"),
                   delai_moyen=("delai_total_j", "mean"),
                   taux_retard=("en_retard", "mean"),
                   delai_douane=("j_douane", "mean"))
              .assign(taux_retard=lambda x: (100 * x["taux_retard"]).round(1),
                      delai_moyen=lambda x: x["delai_moyen"].round(1),
                      delai_douane=lambda x: x["delai_douane"].round(1))
              .sort_values("taux_retard", ascending=False)
              .reset_index())
