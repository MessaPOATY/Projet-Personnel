"""Moteur : lit la configuration YAML, applique les règles et calcule les scores de qualité."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from dq.regles import CATALOGUE

DIMENSIONS = ["Complétude", "Unicité", "Validité", "Cohérence"]


@dataclass
class Resultat:
    jeu: str
    id: str
    description: str
    dimension: str
    severite: str
    lignes_testees: int
    lignes_en_erreur: int
    tolerance_pct: float
    exemples: list[str] = field(default_factory=list)

    @property
    def taux_conformite(self) -> float:
        if self.lignes_testees == 0:
            return 100.0
        return round(100 * (1 - self.lignes_en_erreur / self.lignes_testees), 2)

    @property
    def conforme(self) -> bool:
        return (100 - self.taux_conformite) <= self.tolerance_pct

    def to_dict(self) -> dict:
        return {**asdict(self), "taux_conformite": self.taux_conformite, "conforme": self.conforme}


@dataclass
class Rapport:
    resultats: list[Resultat]
    volumes: dict[str, int]
    seuil_score: float

    @property
    def score_global(self) -> float:
        return round(sum(r.taux_conformite for r in self.resultats) / len(self.resultats), 2)

    def score_par_dimension(self) -> dict[str, float]:
        scores = {}
        for dim in DIMENSIONS:
            taux = [r.taux_conformite for r in self.resultats if r.dimension == dim]
            if taux:
                scores[dim] = round(sum(taux) / len(taux), 2)
        return scores

    @property
    def bloquants_ko(self) -> list[Resultat]:
        return [r for r in self.resultats if r.severite == "bloquant" and not r.conforme]

    @property
    def valide(self) -> bool:
        return not self.bloquants_ko and self.score_global >= self.seuil_score


def charger_config(chemin: Path) -> dict:
    config = yaml.safe_load(Path(chemin).read_text(encoding="utf-8"))
    for nom, jeu in config["jeux_de_donnees"].items():
        for r in jeu["regles"]:
            if r["type"] not in CATALOGUE:
                raise ValueError(f"[{nom}/{r['id']}] type de règle inconnu : {r['type']}")
            if r.get("dimension") not in DIMENSIONS:
                raise ValueError(f"[{nom}/{r['id']}] dimension invalide : {r.get('dimension')}")
    return config


def executer_controles(config: dict, racine: Path = Path(".")) -> Rapport:
    donnees = {nom: pd.read_csv(racine / jeu["fichier"], dtype={jeu["cle"]: str})
               for nom, jeu in config["jeux_de_donnees"].items()}

    resultats = []
    for nom, jeu in config["jeux_de_donnees"].items():
        df = donnees[nom]
        for r in jeu["regles"]:
            params = {k: v for k, v in r.items()
                      if k not in ("id", "type", "description", "dimension", "severite", "tolerance_pct")}
            if "reference" in params:                       # référentiel = un autre jeu de données
                params["reference"] = donnees[params["reference"]]
            en_erreur = CATALOGUE[r["type"]](df, **params)
            resultats.append(Resultat(
                jeu=nom, id=r["id"], description=r["description"], dimension=r["dimension"],
                severite=r.get("severite", "avertissement"), lignes_testees=len(df),
                lignes_en_erreur=int(en_erreur.sum()), tolerance_pct=r.get("tolerance_pct", 0.0),
                exemples=df.loc[en_erreur, jeu["cle"]].astype(str).head(5).tolist(),
            ))
    return Rapport(resultats, {n: len(d) for n, d in donnees.items()}, config.get("seuil_score_global", 95))
