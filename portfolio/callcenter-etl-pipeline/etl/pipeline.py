"""
Point d'entrée du pipeline :  python -m etl.pipeline

Étapes : extraction -> transformation -> contrôle qualité (seuil de rejet)
         -> chargement transactionnel -> journalisation de l'exécution
"""
from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

import duckdb
import yaml

from etl.extract import extraire_tout
from etl.load import charger_rejets, charger_tables, initialiser_schema, journaliser
from etl.transform import transformer

RACINE = Path(__file__).resolve().parents[1]

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
log = logging.getLogger("pipeline")


JOURNAL_DDL = """CREATE TABLE IF NOT EXISTS journal_executions (
    run_id VARCHAR PRIMARY KEY, debut TIMESTAMP, fin TIMESTAMP, lignes_lues INTEGER,
    lignes_chargees INTEGER, lignes_rejetees INTEGER, taux_rejet DOUBLE, statut VARCHAR)"""


class SeuilRejetDepasse(Exception):
    """Levée quand la qualité des données sources est trop dégradée pour charger."""


def executer(config_path: Path = RACINE / "config" / "pipeline.yaml") -> dict:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    debut = datetime.now()
    log.info("Démarrage de l'exécution %s", run_id)

    sources = extraire_tout(RACINE / config["chemins"]["raw"])
    lignes_lues = sum(len(df) for nom, df in sources.items() if nom in ("appels", "enquetes"))

    tables, rejets = transformer(sources)
    taux_rejet = len(rejets) / lignes_lues
    log.info("Rejets : %d lignes (%.2f %%)", len(rejets), taux_rejet * 100)
    for motif, nb in rejets["motif"].value_counts().items():
        log.info("   - %-32s %5d", motif, nb)

    entrepot = RACINE / config["chemins"]["entrepot"]
    entrepot.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(entrepot))

    resume = {"run_id": run_id, "debut": debut, "lignes_lues": lignes_lues,
              "lignes_rejetees": len(rejets), "taux_rejet": round(taux_rejet, 4)}
    try:
        if taux_rejet > config["qualite"]["taux_rejet_max"]:
            raise SeuilRejetDepasse(
                f"Taux de rejet {taux_rejet:.2%} > seuil {config['qualite']['taux_rejet_max']:.2%}"
            )
        con.begin()                       # tout ou rien : pas d'entrepôt à moitié chargé
        initialiser_schema(con, RACINE / "sql" / "schema.sql")
        charge = charger_tables(con, tables)
        charger_rejets(con, rejets, run_id)
        con.commit()
        resume.update(lignes_chargees=charge, statut="SUCCES")
    except Exception as exc:
        try:
            con.rollback()              # annule un chargement partiel éventuel
        except duckdb.Error:
            pass                        # aucune transaction ouverte (échec avant chargement)
        log.error("Échec : %s", exc)
        resume.update(lignes_chargees=0, statut="ECHEC")
        raise
    finally:
        resume["fin"] = datetime.now()
        # Le journal est conservé d'une exécution à l'autre, même en cas d'échec
        con.execute(JOURNAL_DDL)
        journaliser(con, **resume)
        con.close()

    duree = (resume["fin"] - debut).total_seconds()
    log.info("Exécution %s terminée en %.1f s — statut %s", run_id, duree, resume["statut"])
    return resume


if __name__ == "__main__":
    try:
        executer()
    except SeuilRejetDepasse:
        sys.exit(1)
