"""
Génère des dossiers de transit SYNTHÉTIQUES (fictifs) : import de marchandises,
de l'arrivée au port jusqu'à la livraison chez le client.

Chaque dossier passe par 3 étapes dont les durées sont tirées au hasard,
avec des causes de retard réalistes (documents incomplets, inspection douanière,
congestion portuaire, indisponibilité camion…).
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 24
DATA = Path(__file__).resolve().parents[1] / "data"

CLIENTS = ["Agro Congo Négoce", "BTP Atlantique", "Pharma Centrale", "Distrib Express",
           "Mines du Kouilou", "TechImport", "Textiles du Sud", "Auto Pièces Plus"]
MARCHANDISES = {"Matériaux BTP": 1.2, "Produits pharmaceutiques": 0.8, "Pièces automobiles": 1.0,
                "Électronique": 0.9, "Agroalimentaire": 1.1, "Équipements miniers": 1.4}
DESTINATIONS = {"Pointe-Noire": 1, "Dolisie": 2, "Brazzaville": 4, "Nkayi": 2}
CAUSES = ["Documents incomplets", "Inspection douanière", "Congestion portuaire",
          "Camion indisponible", "Paiement des droits tardif", "Route impraticable"]


def main(n: int = 2500) -> None:
    rng = np.random.default_rng(SEED)
    lignes = []
    for i in range(1, n + 1):
        marchandise = str(rng.choice(list(MARCHANDISES)))
        destination = str(rng.choice(list(DESTINATIONS), p=[0.45, 0.15, 0.3, 0.1]))
        mode = str(rng.choice(["Maritime", "Aérien"], p=[0.85, 0.15]))
        arrivee = date(2025, 7, 1) + timedelta(days=int(rng.integers(0, 365)))
        saison_pluies = arrivee.month in (11, 12, 1, 2, 3, 4)

        # Durées « normales » (jours) par étape
        j_port = rng.integers(2, 5) if mode == "Maritime" else rng.integers(0, 2)
        j_douane = rng.integers(2, 5)
        j_transport = DESTINATIONS[destination] + rng.integers(0, 2)

        cause = ""
        alea = rng.random()
        if alea < 0.10:
            cause, j_douane = "Documents incomplets", j_douane + rng.integers(3, 10)
        elif alea < 0.17:
            cause, j_douane = "Inspection douanière", j_douane + rng.integers(2, 7)
        elif alea < 0.23 and mode == "Maritime":
            cause, j_port = "Congestion portuaire", j_port + rng.integers(3, 8)
        elif alea < 0.28:
            cause, j_transport = "Camion indisponible", j_transport + rng.integers(1, 4)
        elif alea < 0.32:
            cause, j_douane = "Paiement des droits tardif", j_douane + rng.integers(2, 6)
        elif saison_pluies and destination != "Pointe-Noire" and alea < 0.45:
            cause, j_transport = "Route impraticable", j_transport + rng.integers(2, 6)
        j_douane = int(round(j_douane * MARCHANDISES[marchandise]))

        sortie_port = arrivee + timedelta(days=int(j_port))
        dedouanement = sortie_port + timedelta(days=int(j_douane))
        livraison = dedouanement + timedelta(days=int(j_transport))
        delai_engage = 10 if destination in ("Pointe-Noire", "Nkayi", "Dolisie") else 12
        if mode == "Aérien":
            delai_engage -= 3

        lignes.append({
            "dossier_id": f"TR{arrivee:%y}-{i:05d}",
            "client": str(rng.choice(CLIENTS)),
            "mode_transport": mode,
            "type_marchandise": marchandise,
            "destination": destination,
            "poids_kg": int(rng.lognormal(8, 1)),
            "date_arrivee": arrivee.isoformat(),
            "date_sortie_port": sortie_port.isoformat(),
            "date_dedouanement": dedouanement.isoformat(),
            "date_livraison_prevue": (arrivee + timedelta(days=delai_engage)).isoformat(),
            "date_livraison": livraison.isoformat(),
            "cause_retard_declaree": cause,
        })
    DATA.mkdir(exist_ok=True)
    pd.DataFrame(lignes).to_csv(DATA / "dossiers_transit.csv", index=False)
    print(f"{n} dossiers générés dans {DATA}")


if __name__ == "__main__":
    main()
