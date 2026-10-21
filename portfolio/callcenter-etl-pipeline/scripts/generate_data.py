"""
Génère des données SYNTHÉTIQUES (100 % fictives) d'un centre de contact multi-clients.

Les fichiers sont volontairement "sales" (formats de dates mélangés, doublons,
libellés incohérents, valeurs aberrantes, références manquantes) afin de
reproduire les problèmes rencontrés sur des données réelles et de justifier
l'étape de transformation du pipeline.

Sources produites dans data/raw/ :
    - appels.csv               (CSV ; séparateur ";")  -> interactions clients
    - agents.json              (JSON)                  -> référentiel RH des agents
    - campagnes.xlsx           (Excel)                 -> référentiel des campagnes clients
    - enquetes_satisfaction.csv (CSV)                  -> réponses aux enquêtes CSAT
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

PRENOMS = ["Camille", "Lucas", "Inès", "Hugo", "Aïcha", "Nathan", "Léa", "Yanis", "Chloé", "Mamadou",
           "Sarah", "Théo", "Fatou", "Louis", "Emma", "Karim", "Manon", "Enzo", "Awa", "Jules"]
NOMS = ["Martin", "Bernard", "Diallo", "Petit", "Durand", "Leroy", "Moreau", "Simon", "Ndiaye", "Laurent",
        "Michel", "Garcia", "Traoré", "Roux", "Fournier", "Mercier", "Blanc", "Faure", "Kone", "Girard"]
SITES = ["Poitiers", "Lyon", "Marseille", "Lille"]
EQUIPES = ["Niveau 1", "Niveau 2", "Back-office"]

CAMPAGNES = [
    ("CMP01", "Énergie Plus", "Énergie", 4.0),
    ("CMP02", "TelcoNova", "Télécom", 3.8),
    ("CMP03", "Banque Horizon", "Banque", 4.2),
    ("CMP04", "AssurVie", "Assurance", 4.1),
    ("CMP05", "MobiTrans", "Transport", 3.9),
    ("CMP06", "E-Shop Express", "E-commerce", 4.0),
]

# Variantes "sales" des libellés, comme on en trouve en sortie d'outils différents
CANAL_VARIANTES = {
    "telephone": ["Téléphone", "telephone", "TEL", " téléphone "],
    "chat": ["Chat", "chat", "CHAT "],
    "email": ["Email", "e-mail", "MAIL"],
}
STATUT_VARIANTES = {
    "decroche": ["Décroché", "decroche", "DECROCHE"],
    "abandonne": ["Abandonné", "abandon", "ABANDONNE"],
}


def generer_agents(rng: np.random.Generator, n: int = 40) -> list[dict]:
    agents = []
    for i in range(1, n + 1):
        embauche = datetime(2021, 1, 1) + timedelta(days=int(rng.integers(0, 1800)))
        agents.append({
            "agent_id": f"AG{i:03d}",
            "prenom": str(rng.choice(PRENOMS)),
            "nom": str(rng.choice(NOMS)),
            "site": str(rng.choice(SITES, p=[0.4, 0.25, 0.2, 0.15])),
            "equipe": str(rng.choice(EQUIPES, p=[0.6, 0.25, 0.15])),
            "date_embauche": embauche.strftime("%Y-%m-%d"),
        })
    return agents


def generer_campagnes() -> pd.DataFrame:
    return pd.DataFrame(
        [{"campagne_id": c, "client": cl, "secteur": s, "objectif_csat": o,
          "date_debut": "2025-09-01"} for c, cl, s, o in CAMPAGNES]
    )


def generer_appels(rng: np.random.Generator, agents: list[dict], n: int = 20_000) -> pd.DataFrame:
    debut = datetime(2026, 1, 1)
    agent_ids = [a["agent_id"] for a in agents]
    campagne_ids = [c[0] for c in CAMPAGNES]

    lignes = []
    for i in range(1, n + 1):
        jour = debut + timedelta(days=int(rng.integers(0, 181)))
        horodatage = jour.replace(hour=int(rng.integers(8, 20)), minute=int(rng.integers(0, 60)),
                                  second=int(rng.integers(0, 60)))
        canal = str(rng.choice(["telephone", "chat", "email"], p=[0.65, 0.25, 0.10]))

        if canal == "email":
            attente = np.nan
            abandon = False
        else:
            moyenne = 50 if canal == "telephone" else 25
            # Plus d'attente le lundi et entre 12h et 14h : saisonnalité réaliste
            if horodatage.weekday() == 0:
                moyenne *= 1.5
            if 12 <= horodatage.hour < 14:
                moyenne *= 1.3
            attente = float(round(rng.exponential(moyenne)))
            abandon = rng.random() < min(0.6, attente / 600)

        traitement = 0.0 if abandon else float(round(rng.lognormal(mean=5.6, sigma=0.5)))
        resolu = None if abandon else bool(rng.random() < 0.74)

        lignes.append({
            "appel_id": f"APL{i:06d}",
            "date_heure": horodatage,
            "canal": canal,
            "agent_id": None if abandon else str(rng.choice(agent_ids)),
            "campagne_id": str(rng.choice(campagne_ids)),
            "numero_client": f"0{rng.integers(6, 8)}{rng.integers(10_000_000, 99_999_999)}",
            "duree_attente_s": attente,
            "duree_traitement_s": traitement,
            "statut": "abandonne" if abandon else "decroche",
            "resolu_1er_contact": resolu,
        })
    return pd.DataFrame(lignes)


def salir_appels(rng: np.random.Generator, df: pd.DataFrame) -> pd.DataFrame:
    """Introduit volontairement des anomalies typiques."""
    df = df.copy()
    n = len(df)

    # 1. Formats de dates hétérogènes (exports de 3 outils différents)
    tirage = rng.random(n)
    dates = []
    for d, t in zip(df["date_heure"], tirage):
        if t < 0.85:
            dates.append(d.strftime("%Y-%m-%d %H:%M:%S"))
        elif t < 0.95:
            dates.append(d.strftime("%d/%m/%Y %H:%M"))
        elif t < 0.995:
            dates.append(d.strftime("%Y-%m-%dT%H:%M:%S"))
        else:
            dates.append("date inconnue")
    df["date_heure"] = dates

    # 2. Libellés incohérents
    df["canal"] = [str(rng.choice(CANAL_VARIANTES[c])) for c in df["canal"]]
    df["statut"] = [str(rng.choice(STATUT_VARIANTES[s])) for s in df["statut"]]
    df["resolu_1er_contact"] = [
        "" if r is None else str(rng.choice(["Oui", "1", "TRUE"] if r else ["Non", "0", "FALSE"]))
        for r in df["resolu_1er_contact"]
    ]

    # 3. Durées négatives (bug d'horodatage côté téléphonie)
    idx = rng.choice(n, size=int(n * 0.005), replace=False)
    df.loc[idx, "duree_traitement_s"] = -df.loc[idx, "duree_traitement_s"].abs() - 1

    # 4. Agents absents du référentiel
    decroches = df.index[df["agent_id"].notna()]
    idx = rng.choice(decroches, size=int(n * 0.005), replace=False)
    df.loc[idx, "agent_id"] = "AG999"

    # 5. Doublons (double export d'un même lot)
    doublons = df.sample(frac=0.01, random_state=SEED)
    df = pd.concat([df, doublons], ignore_index=True)
    return df.sample(frac=1, random_state=SEED).reset_index(drop=True)


def generer_enquetes(rng: np.random.Generator, appels: pd.DataFrame) -> pd.DataFrame:
    """~30 % des clients servis répondent à l'enquête ; la note dépend de la résolution et de l'attente."""
    servis = appels[appels["statut"] == "decroche"]
    repondants = servis.sample(frac=0.30, random_state=SEED)
    notes = []
    for _, r in repondants.iterrows():
        base = 4.3 if r["resolu_1er_contact"] else 2.8
        attente = 0 if pd.isna(r["duree_attente_s"]) else r["duree_attente_s"]
        base -= min(1.2, attente / 300)
        notes.append(int(np.clip(round(rng.normal(base, 0.8)), 1, 5)))
    enq = pd.DataFrame({"appel_id": repondants["appel_id"].values, "note_csat": notes})
    enq["note_csat"] = enq["note_csat"].astype(object)

    # Anomalies : notes hors échelle et valeurs non numériques
    idx = rng.choice(len(enq), size=int(len(enq) * 0.01), replace=False)
    enq.loc[idx, "note_csat"] = [str(rng.choice(["0", "6", "N/A", "10"])) for _ in idx]
    return enq


def main() -> None:
    rng = np.random.default_rng(SEED)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    agents = generer_agents(rng)
    (RAW_DIR / "agents.json").write_text(json.dumps(agents, ensure_ascii=False, indent=2), encoding="utf-8")

    generer_campagnes().to_excel(RAW_DIR / "campagnes.xlsx", index=False)

    appels_propres = generer_appels(rng, agents)
    generer_enquetes(rng, appels_propres).to_csv(RAW_DIR / "enquetes_satisfaction.csv", index=False)
    salir_appels(rng, appels_propres).to_csv(RAW_DIR / "appels.csv", sep=";", index=False)

    print(f"Données synthétiques générées dans {RAW_DIR}")


if __name__ == "__main__":
    main()
