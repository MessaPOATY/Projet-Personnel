"""
Utilisation :
    python -m dq.cli --config config/regles_rh.yaml --sortie rapports/

Code retour 0 si les données sont validées, 1 sinon : le contrôle peut donc
bloquer automatiquement une étape d'un pipeline ou d'une CI.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dq.moteur import charger_config, executer_controles
from dq.rapport import exporter_html, exporter_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Contrôle qualité de jeux de données à partir de règles YAML")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--sortie", default=Path("rapports"), type=Path)
    args = parser.parse_args(argv)

    rapport = executer_controles(charger_config(args.config))
    args.sortie.mkdir(parents=True, exist_ok=True)
    exporter_html(rapport, args.sortie / "rapport_qualite.html")
    exporter_json(rapport, args.sortie / "rapport_qualite.json")

    print(f"Score global : {rapport.score_global:.2f} %")
    for dim, score in rapport.score_par_dimension().items():
        print(f"  {dim:<12} {score:6.2f} %")
    for r in rapport.resultats:
        statut = "OK " if r.conforme else ("KO " if r.severite == "bloquant" else "!! ")
        print(f"  [{statut}] {r.id:<8} {r.lignes_en_erreur:>5} erreur(s)  {r.description}")
    print("VALIDÉ" if rapport.valide else f"BLOQUÉ : {len(rapport.bloquants_ko)} contrôle(s) bloquant(s) en échec")
    print(f"Rapport : {args.sortie / 'rapport_qualite.html'}")
    return 0 if rapport.valide else 1


if __name__ == "__main__":
    sys.exit(main())
