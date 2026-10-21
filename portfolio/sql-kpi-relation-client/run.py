"""
Mini-orchestrateur SQL inspiré de dbt, sur DuckDB.

    python run.py build      charge les données brutes, construit les modèles, lance les tests SQL
    python run.py analyses   exécute les requêtes d'analyse et exporte les résultats

Conventions :
  - models/<couche>/<nom>.sql contient UN SELECT ; il est matérialisé en table <couche>.<nom>
  - les couches sont construites dans l'ordre : staging -> intermediate -> marts
  - tests/<nom>.sql renvoie les lignes EN ERREUR : un test réussi renvoie 0 ligne
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import duckdb

RACINE = Path(__file__).resolve().parent
BASE = RACINE / "data" / "relation_client.duckdb"
COUCHES = ["staging", "intermediate", "marts"]


def connecter() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(BASE))


def charger_brut(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    for fichier in sorted((RACINE / "data").glob("*.csv")):
        con.execute(f"CREATE OR REPLACE TABLE raw.{fichier.stem} AS "
                    f"SELECT * FROM read_csv_auto('{fichier.as_posix()}', header=true)")
        n = con.execute(f"SELECT COUNT(*) FROM raw.{fichier.stem}").fetchone()[0]
        print(f"  raw.{fichier.stem:<28} {n:>8} lignes")


def construire_modeles(con: duckdb.DuckDBPyConnection) -> None:
    for couche in COUCHES:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {couche}")
        for fichier in sorted((RACINE / "models" / couche).glob("*.sql")):
            t0 = time.perf_counter()
            requete = fichier.read_text(encoding="utf-8").strip().rstrip(";")
            con.execute(f"CREATE OR REPLACE TABLE {couche}.{fichier.stem} AS {requete}")
            n = con.execute(f"SELECT COUNT(*) FROM {couche}.{fichier.stem}").fetchone()[0]
            print(f"  {couche}.{fichier.stem:<{40 - len(couche)}} {n:>8} lignes  ({time.perf_counter() - t0:.2f} s)")


def lancer_tests(con: duckdb.DuckDBPyConnection) -> bool:
    succes = True
    for fichier in sorted((RACINE / "tests").glob("*.sql")):
        erreurs = con.execute(fichier.read_text(encoding="utf-8")).fetchall()
        statut = "OK  " if not erreurs else f"ÉCHEC ({len(erreurs)} ligne(s))"
        print(f"  [{statut}] {fichier.stem}")
        succes &= not erreurs
    return succes


def lancer_analyses(con: duckdb.DuckDBPyConnection) -> None:
    sortie = RACINE / "resultats"
    sortie.mkdir(exist_ok=True)
    for fichier in sorted((RACINE / "analyses").glob("*.sql")):
        df = con.execute(fichier.read_text(encoding="utf-8")).df()
        df.to_csv(sortie / f"{fichier.stem}.csv", index=False)
        print(f"\n=== {fichier.stem} ===")
        print(df.head(12).to_string(index=False))


def main(commande: str) -> int:
    con = connecter()
    try:
        if commande == "build":
            print("1. Chargement des données brutes");  charger_brut(con)
            print("2. Construction des modèles");       construire_modeles(con)
            print("3. Tests de données")
            return 0 if lancer_tests(con) else 1
        if commande == "analyses":
            lancer_analyses(con)
            return 0
        print(__doc__)
        return 2
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
