"""
Génère un extrait SYNTHÉTIQUE (fictif) de SIRH : salariés + services.
Des anomalies sont injectées volontairement, en proportions connues,
pour vérifier que le framework les détecte toutes.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 7
DATA = Path(__file__).resolve().parents[1] / "data"

PRENOMS = ["Camille", "Lucas", "Inès", "Hugo", "Aïcha", "Nathan", "Léa", "Yanis", "Chloé", "Mamadou",
           "Sarah", "Théo", "Fatou", "Louis", "Emma", "Karim", "Manon", "Enzo", "Awa", "Jules"]
NOMS = ["Martin", "Bernard", "Diallo", "Petit", "Durand", "Leroy", "Moreau", "Simon", "Ndiaye", "Laurent",
        "Michel", "Garcia", "Traoré", "Roux", "Fournier", "Mercier", "Blanc", "Faure", "Kone", "Girard"]
SERVICES = [("S01", "Relation client N1", "Poitiers"), ("S02", "Relation client N2", "Poitiers"),
            ("S03", "Back-office", "Lyon"), ("S04", "Ressources humaines", "Poitiers"),
            ("S05", "Finance", "Paris"), ("S06", "DSI", "Poitiers"), ("S07", "Qualité", "Lille")]
CODES_POSTAUX = ["86000", "86180", "86360", "69003", "69007", "75011", "59000", "13001"]


def sans_accents(s: str) -> str:
    return s.lower().translate(str.maketrans("àâäéèêëïîôöùûüç", "aaaeeeeiioouuuc"))


def generer(n: int = 1500) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    lignes = []
    for i in range(1, n + 1):
        prenom, nom = str(rng.choice(PRENOMS)), str(rng.choice(NOMS))
        naissance = date(1965, 1, 1) + timedelta(days=int(rng.integers(0, 365 * 40)))
        entree = date(2015, 1, 1) + timedelta(days=int(rng.integers(0, 365 * 11)))
        contrat = str(rng.choice(["CDI", "CDD", "Alternance", "Intérim"], p=[0.7, 0.15, 0.08, 0.07]))
        sortie = entree + timedelta(days=int(rng.integers(90, 900))) if contrat != "CDI" and rng.random() < 0.6 else None
        temps = float(rng.choice([1.0, 0.8, 0.5], p=[0.8, 0.15, 0.05]))
        salaire = round(float(rng.normal(28000, 5000)) if contrat != "Alternance" else float(rng.normal(14000, 2000)), -1)
        lignes.append({
            "matricule": f"M{i:05d}", "prenom": prenom, "nom": nom,
            "email": f"{sans_accents(prenom)}.{sans_accents(nom)}{i}@entreprise-demo.fr",
            "date_naissance": naissance.isoformat(), "date_entree": entree.isoformat(),
            "date_sortie": sortie.isoformat() if sortie else "",
            "service_id": SERVICES[int(rng.integers(0, len(SERVICES)))][0],
            "type_contrat": contrat, "temps_travail": temps,
            "salaire_brut_annuel": max(salaire, 21700) if contrat != "Alternance" else salaire,
            "manager_matricule": f"M{int(rng.integers(1, 60)):05d}" if i > 60 else "",
            "code_postal": str(rng.choice(CODES_POSTAUX)),
        })
    df = pd.DataFrame(lignes)

    def piocher(k):
        return rng.choice(df.index[60:], size=k, replace=False)

    # --- Anomalies injectées (nombre connu) ---------------------------------
    df.loc[piocher(12), "email"] = ["prenom.nom@", "sans-arobase.fr", "a@b"] * 4          # format email
    df.loc[piocher(8), "service_id"] = ""                                                   # complétude
    df.loc[piocher(5), "service_id"] = "S99"                                                # service inexistant
    df.loc[piocher(6), "type_contrat"] = ["cdi", "Stage ", "CDI "] * 2                      # valeurs non standard
    idx = piocher(7)
    df.loc[idx, "date_sortie"] = (pd.to_datetime(df.loc[idx, "date_entree"]) - pd.Timedelta(days=30)).dt.strftime("%Y-%m-%d")
    df.loc[piocher(4), "date_naissance"] = "2031-05-12"                                     # date future
    df.loc[piocher(3), "salaire_brut_annuel"] = -1                                          # valeur aberrante
    df.loc[piocher(5), "salaire_brut_annuel"] = 15000.0                                     # < SMIC pour un CDI
    df.loc[piocher(9), "manager_matricule"] = "M99999"                                      # manager inexistant
    df.loc[piocher(6), "code_postal"] = ["8600", "ABCDE", "860000"] * 2
    doublons = df.loc[piocher(4)].copy()                                                    # matricules en double
    df = pd.concat([df, doublons], ignore_index=True)

    services = pd.DataFrame(SERVICES, columns=["service_id", "libelle", "site"])
    return df, services


def main() -> None:
    DATA.mkdir(exist_ok=True)
    salaries, services = generer()
    salaries.to_csv(DATA / "salaries.csv", index=False)
    services.to_csv(DATA / "services.csv", index=False)
    print(f"{len(salaries)} salariés et {len(services)} services générés dans {DATA}")


if __name__ == "__main__":
    main()
