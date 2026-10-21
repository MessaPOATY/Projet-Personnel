"""
Utilisation :
    export RGPD_CLE_PSEUDO="une-cle-longue-et-secrete"
    python -m rgpd.cli --entree data/reclamations_brut.csv --politique config/politique_reclamations.yaml

Étapes : détection des DCP -> vérification que chaque DCP a une règle -> application de la politique
         -> contrôle d'absence de DCP résiduelle -> k-anonymat -> export + fiche de traitement
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd
import yaml

from rgpd import k_anonymat
from rgpd.detection import detecter
from rgpd.registre import generer_fiche
from rgpd.transformations import appliquer_politique


class PolitiqueIncomplete(Exception):
    pass


class FuiteDetectee(Exception):
    pass


def traiter(entree: Path, politique_path: Path, sortie_dir: Path) -> dict:
    config = yaml.safe_load(politique_path.read_text(encoding="utf-8"))
    df = pd.read_csv(entree, dtype=str, keep_default_na=False)

    # 1. Détection
    detections = detecter(df)
    print(f"1. {len(detections)} colonne(s) contenant des données personnelles détectée(s) :")
    for d in detections:
        print(f"   - {d.colonne:<20} {d.categorie:<18} [{d.niveau}]  via {d.signal}")

    # 2. Aucune DCP détectée ne doit être oubliée par la politique
    oubliees = [d.colonne for d in detections if d.colonne not in config["colonnes"]]
    if oubliees:
        raise PolitiqueIncomplete(f"DCP sans règle dans la politique : {oubliees}")

    # 3. Application
    protege = appliquer_politique(df, config["colonnes"])
    print(f"2. Politique appliquée : {df.shape[1]} -> {protege.shape[1]} colonnes")

    # 4. Contrôle de fuite : plus aucun motif de DCP directe ne doit subsister
    residus = [d for d in detecter(protege) if d.signal != "nom de colonne"]
    if residus:
        raise FuiteDetectee(f"DCP résiduelles : {[(d.colonne, d.categorie) for d in residus]}")
    print("3. Contrôle de fuite : aucune DCP directe résiduelle ✔")

    # 5. k-anonymat
    ka = config["k_anonymat"]
    k_avant = k_anonymat.evaluer(protege, ka["quasi_identifiants"], ka["k_cible"])
    if not k_avant["conforme"] and ka.get("supprimer_classes_rares"):
        protege = k_anonymat.supprimer_classes_rares(protege, ka["quasi_identifiants"], ka["k_cible"])
    k_apres = k_anonymat.evaluer(protege, ka["quasi_identifiants"], ka["k_cible"])
    print(f"4. k-anonymat : k = {k_avant['k_obtenu']} -> {k_apres['k_obtenu']} "
          f"({k_avant['personnes_a_risque']} ligne(s) à risque retirée(s))")

    # 6. Export + documentation
    sortie_dir.mkdir(parents=True, exist_ok=True)
    fichier = sortie_dir / f"{entree.stem.replace('_brut', '')}_pseudonymise.csv"
    protege.to_csv(fichier, index=False)
    empreinte = hashlib.sha256(fichier.read_bytes()).hexdigest()
    volumes = {"entree": len(df), "sortie": len(protege),
               "colonnes_entree": df.shape[1], "colonnes_sortie": protege.shape[1]}
    fiche = sortie_dir / "fiche_traitement.md"
    fiche.write_text(generer_fiche(config, detections, k_avant, k_apres, volumes, empreinte), encoding="utf-8")
    print(f"5. Export : {fichier}\n   Fiche de traitement : {fiche}")
    return {"fichier": fichier, "k_apres": k_apres, "volumes": volumes}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pseudonymisation d'un export selon une politique RGPD")
    p.add_argument("--entree", required=True, type=Path)
    p.add_argument("--politique", required=True, type=Path)
    p.add_argument("--sortie", default=Path("sortie"), type=Path)
    args = p.parse_args(argv)
    try:
        traiter(args.entree, args.politique, args.sortie)
        return 0
    except (PolitiqueIncomplete, FuiteDetectee, RuntimeError) as e:
        print(f"⛔ ARRÊT : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
