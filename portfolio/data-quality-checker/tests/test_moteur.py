"""Le framework doit retrouver EXACTEMENT les anomalies injectées par le générateur."""
from pathlib import Path

import pytest

from dq.cli import main
from dq.moteur import charger_config, executer_controles

RACINE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def rapport():
    return executer_controles(charger_config(RACINE / "config/regles_rh.yaml"), racine=RACINE)


@pytest.mark.parametrize("regle, attendu", [
    ("SAL-02", 8),    # services vides
    ("SAL-03", 8),    # 4 matricules dupliqués -> 8 lignes concernées
    ("SAL-04", 12),   # emails invalides
    ("SAL-05", 6),    # types de contrat hors référentiel
    ("SAL-07", 4),    # dates de naissance futures
    ("SAL-08", 3),    # salaires négatifs
    ("SAL-09", 7),    # sortie avant entrée
    ("SAL-10", 5),    # service inexistant
])
def test_anomalies_injectees_detectees(rapport, regle, attendu):
    resultat = next(r for r in rapport.resultats if r.id == regle)
    assert resultat.lignes_en_erreur == attendu


def test_publication_bloquee(rapport):
    assert not rapport.valide
    assert {r.id for r in rapport.bloquants_ko} >= {"SAL-03", "SAL-05", "SAL-09"}


def test_config_invalide_refusee(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text("jeux_de_donnees:\n  x:\n    fichier: a.csv\n    cle: id\n    regles:\n"
                   "      - {id: X1, type: inexistante, dimension: Validité, description: test}\n")
    with pytest.raises(ValueError, match="type de règle inconnu"):
        charger_config(cfg)


def test_cli_code_retour_et_rapports(tmp_path, monkeypatch):
    monkeypatch.chdir(RACINE)
    assert main(["--config", "config/regles_rh.yaml", "--sortie", str(tmp_path)]) == 1
    assert (tmp_path / "rapport_qualite.html").exists()
    assert (tmp_path / "rapport_qualite.json").exists()
