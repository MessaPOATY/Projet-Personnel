"""
Génère des données SYNTHÉTIQUES (fictives) d'interactions de relation client,
au format d'extraction brute d'un outil de téléphonie / CRM.

    data/interactions.csv   1 ligne = 1 interaction
    data/agents.csv         référentiel agents
    data/campagnes.csv      référentiel campagnes + objectifs contractuels (SLA)
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2026
DATA = Path(__file__).resolve().parents[1] / "data"

CAMPAGNES = [
    # id, client, secteur, objectif SLA (% décrochés < 60 s), objectif FCR
    ("CMP01", "Énergie Plus", "Énergie", 0.80, 0.65),
    ("CMP02", "TelcoNova", "Télécom", 0.75, 0.60),
    ("CMP03", "Banque Horizon", "Banque", 0.85, 0.68),
    ("CMP04", "AssurVie", "Assurance", 0.75, 0.65),
    ("CMP05", "MobiTrans", "Transport", 0.70, 0.62),
]
# Effets propres à chaque campagne (cachés) : sous-effectif chronique, complexité des demandes
FACTEUR_ATTENTE = np.array([0.85, 1.25, 0.65, 1.05, 0.9])
BONUS_RESOLUTION = np.array([0.03, -0.06, 0.06, 0.0, -0.02])
SITES = ["Poitiers", "Lyon", "Lille"]


def main(n_interactions: int = 60_000, n_clients: int = 15_000) -> None:
    rng = np.random.default_rng(SEED)
    DATA.mkdir(exist_ok=True)

    # --- Agents : chaque agent a un "niveau" caché qui influence ses résultats
    agents = pd.DataFrame({
        "agent_id": [f"AG{i:03d}" for i in range(1, 61)],
        "site": rng.choice(SITES, 60, p=[0.5, 0.3, 0.2]),
        "date_embauche": [(datetime(2022, 1, 1) + timedelta(days=int(d))).date()
                          for d in rng.integers(0, 1500, 60)],
    })
    anciennete_mois = (pd.Timestamp("2026-06-30") - pd.to_datetime(agents["date_embauche"])).dt.days / 30
    niveau = np.clip(0.62 + anciennete_mois / 400 + rng.normal(0, 0.05, 60), 0.5, 0.92)

    campagnes = pd.DataFrame(CAMPAGNES, columns=["campagne_id", "client", "secteur", "objectif_sla", "objectif_fcr"])

    # --- Interactions
    debut = datetime(2026, 1, 1)
    jours = rng.integers(0, 181, n_interactions)
    dates = np.array([debut + timedelta(days=int(j)) for j in jours])
    jour_semaine = np.array([d.weekday() for d in dates])
    # Profil horaire : pics à 10h et 14h
    heures = rng.choice(range(8, 20), n_interactions,
                        p=np.array([4, 8, 12, 10, 7, 6, 10, 9, 8, 6, 4, 3]) / 87)
    horodatages = [d.replace(hour=int(h), minute=int(m), second=int(s))
                   for d, h, m, s in zip(dates, heures, rng.integers(0, 60, n_interactions),
                                          rng.integers(0, 60, n_interactions))]

    canal = rng.choice(["Téléphone", "Chat", "Email"], n_interactions, p=[0.65, 0.25, 0.10])
    idx_campagne = rng.integers(0, len(CAMPAGNES), n_interactions)
    charge = (1 + 0.6 * (jour_semaine == 0) + 0.4 * np.isin(heures, [10, 14])) * FACTEUR_ATTENTE[idx_campagne]
    attente = np.where(canal == "Email", np.nan, np.round(rng.exponential(35 * charge)))
    abandon = (canal != "Email") & (rng.random(n_interactions) < np.minimum(0.5, np.nan_to_num(attente) / 500))

    idx_agent = rng.integers(0, 60, n_interactions)
    proba_resolution = np.clip(niveau[idx_agent] + BONUS_RESOLUTION[idx_campagne], 0, 1)
    resolu = (~abandon) & (rng.random(n_interactions) < proba_resolution)
    traitement = np.where(abandon, 0, np.round(rng.lognormal(5.5, 0.45, n_interactions)))
    csat_brut = np.where(resolu, 4.4, 2.9) - np.nan_to_num(attente) / 250 + rng.normal(0, 0.7, n_interactions)
    repond = (~abandon) & (rng.random(n_interactions) < 0.3)

    interactions = pd.DataFrame({
        "interaction_id": [f"INT{i:06d}" for i in range(1, n_interactions + 1)],
        "horodatage": horodatages,
        "client_id": [f"CLI{c:05d}" for c in rng.integers(1, n_clients + 1, n_interactions)],
        "campagne_id": campagnes["campagne_id"].values[idx_campagne],
        "canal": canal,
        "agent_id": np.where(abandon, None, agents["agent_id"].values[idx_agent]),
        "attente_s": attente,
        "traitement_s": traitement,
        "abandonne": abandon,
        "resolu": np.where(abandon, None, resolu),
        "note_csat": np.where(repond, np.clip(np.round(csat_brut), 1, 5), np.nan),
    })

    # --- Recontacts : un client non satisfait rappelle dans les jours qui suivent.
    # Une partie des demandes « déclarées résolues » par l'agent ne l'étaient pas vraiment.
    rappel = ((~abandon) & ~resolu & (rng.random(n_interactions) < 0.45)) | \
             (resolu & (rng.random(n_interactions) < 0.08)) | \
             (abandon & (rng.random(n_interactions) < 0.6))
    suivis = interactions[np.asarray(rappel, dtype=bool)].copy()
    # Rappel 1 à 6 jours plus tard, pendant les heures d'ouverture (8h-20h)
    suivis["horodatage"] = (suivis["horodatage"].dt.normalize()
                            + pd.to_timedelta(rng.integers(1, 7, len(suivis)), unit="D")
                            + pd.to_timedelta(rng.integers(8 * 3600, 20 * 3600, len(suivis)), unit="s"))
    suivis = suivis[suivis["horodatage"] < datetime(2026, 7, 1)]
    suivis["agent_id"] = agents["agent_id"].values[rng.integers(0, 60, len(suivis))]
    suivis["attente_s"] = np.where(suivis["canal"] == "Email", np.nan, np.round(rng.exponential(40, len(suivis))))
    suivis["abandonne"] = False
    suivis["traitement_s"] = np.round(rng.lognormal(5.7, 0.45, len(suivis)))
    suivis["resolu"] = rng.random(len(suivis)) < 0.7
    suivis["note_csat"] = np.where(rng.random(len(suivis)) < 0.3, rng.choice([1, 2, 3, 4], len(suivis)), np.nan)

    interactions = pd.concat([interactions, suivis]).sort_values("horodatage").reset_index(drop=True)
    interactions["interaction_id"] = [f"INT{i:06d}" for i in range(1, len(interactions) + 1)]

    interactions.to_csv(DATA / "interactions.csv", index=False)
    agents.to_csv(DATA / "agents.csv", index=False)
    campagnes.to_csv(DATA / "campagnes.csv", index=False)
    print(f"{len(interactions)} interactions générées dans {DATA}")


if __name__ == "__main__":
    main()
