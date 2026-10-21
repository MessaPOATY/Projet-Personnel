"""Chargement : écriture du modèle en étoile dans DuckDB (rechargement complet, idempotent)."""
from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import pandas as pd

log = logging.getLogger(__name__)

# Ordre important : les dimensions avant la table de faits (clés étrangères)
ORDRE_CHARGEMENT = ["dim_date", "dim_agent", "dim_campagne", "fait_interactions"]


def initialiser_schema(con: duckdb.DuckDBPyConnection, fichier_sql: Path) -> None:
    con.execute(fichier_sql.read_text(encoding="utf-8"))


def charger_tables(con: duckdb.DuckDBPyConnection, tables: dict[str, pd.DataFrame]) -> int:
    total = 0
    for nom in ORDRE_CHARGEMENT:
        df = tables[nom]
        colonnes = ", ".join(df.columns)
        con.register("tmp_df", df)
        con.execute(f"INSERT INTO {nom} ({colonnes}) SELECT {colonnes} FROM tmp_df")
        con.unregister("tmp_df")
        log.info("%-18s : %6d lignes chargées", nom, len(df))
        total += len(df)
    return total


def charger_rejets(con: duckdb.DuckDBPyConnection, rejets: pd.DataFrame, run_id: str) -> None:
    rejets = rejets.assign(run_id=run_id)[["run_id", "source", "cle", "motif", "ligne_brute"]]
    con.register("tmp_rejets", rejets)
    con.execute("INSERT INTO rejets SELECT * FROM tmp_rejets")
    con.unregister("tmp_rejets")


def journaliser(con: duckdb.DuckDBPyConnection, **infos) -> None:
    con.execute(
        "INSERT INTO journal_executions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [infos["run_id"], infos["debut"], infos["fin"], infos["lignes_lues"],
         infos["lignes_chargees"], infos["lignes_rejetees"], infos["taux_rejet"], infos["statut"]],
    )
