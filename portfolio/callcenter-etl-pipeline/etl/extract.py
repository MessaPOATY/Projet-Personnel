"""Extraction : lecture des sources hétérogènes (CSV, JSON, Excel) sans transformation métier."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


def lire_appels(chemin: Path) -> pd.DataFrame:
    # Tout est lu en texte : le typage est fait explicitement dans transform.py
    df = pd.read_csv(chemin, sep=";", dtype=str, keep_default_na=False, encoding="utf-8")
    log.info("appels.csv : %d lignes lues", len(df))
    return df


def lire_agents(chemin: Path) -> pd.DataFrame:
    df = pd.DataFrame(json.loads(chemin.read_text(encoding="utf-8")))
    log.info("agents.json : %d agents lus", len(df))
    return df


def lire_campagnes(chemin: Path) -> pd.DataFrame:
    df = pd.read_excel(chemin, dtype={"campagne_id": str})
    log.info("campagnes.xlsx : %d campagnes lues", len(df))
    return df


def lire_enquetes(chemin: Path) -> pd.DataFrame:
    df = pd.read_csv(chemin, dtype=str, keep_default_na=False)
    log.info("enquetes_satisfaction.csv : %d réponses lues", len(df))
    return df


def extraire_tout(dossier_raw: Path) -> dict[str, pd.DataFrame]:
    return {
        "appels": lire_appels(dossier_raw / "appels.csv"),
        "agents": lire_agents(dossier_raw / "agents.json"),
        "campagnes": lire_campagnes(dossier_raw / "campagnes.xlsx"),
        "enquetes": lire_enquetes(dossier_raw / "enquetes_satisfaction.csv"),
    }
