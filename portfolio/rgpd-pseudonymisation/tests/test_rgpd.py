from datetime import date
from pathlib import Path

import pandas as pd
import pytest
import yaml

from rgpd import k_anonymat
from rgpd.cli import PolitiqueIncomplete, traiter
from rgpd.detection import caviarder_texte, detecter
from rgpd.transformations import (generaliser_age, generaliser_code_postal, masquer_email,
                                  masquer_telephone, pseudonymiser)

RACINE = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def cle(monkeypatch):
    monkeypatch.setenv("RGPD_CLE_PSEUDO", "cle-de-test")


# ---------------------------------------------------------------- détection
def test_detection_par_contenu_meme_avec_un_nom_de_colonne_anodin():
    df = pd.DataFrame({"champ_libre": ["a.b@mail.fr", "x@y.com", "rien"], "montant": ["1", "2", "3"]})
    detections = {d.colonne: d.categorie for d in detecter(df)}
    assert detections == {"champ_libre": "email"}


def test_detection_iban_et_nir_classes_sensibles():
    df = pd.DataFrame({"rib": ["FR76 1234 5678 9012 3456 7890 123"],
                       "x": ["1 85 03 86 123 456 78"]})
    niveaux = {d.colonne: d.niveau for d in detecter(df)}
    assert niveaux == {"rib": "sensible", "x": "sensible"}


@pytest.mark.parametrize("texte, attendu", [
    ("Rappeler au 06 12 34 56 78 svp", "Rappeler au [TELEPHONE] svp"),
    ("Écrire à jean.d@mail.fr", "Écrire à [EMAIL]"),
    ("Virement sur FR76 1234 5678 9012 3456 7890 123.", "Virement sur [IBAN]."),
    ("Commande n° 12345 livrée", "Commande n° 12345 livrée"),        # pas de faux positif
])
def test_caviardage_texte_libre(texte, attendu):
    assert caviarder_texte(texte) == attendu


# ---------------------------------------------------------------- transformations
def test_pseudonymisation_deterministe_et_dependante_de_la_cle(monkeypatch):
    s = pd.Series(["C001", "C002", "C001", ""])
    p1 = pseudonymiser(s, prefixe="CLI")
    assert p1[0] == p1[2] and p1[0] != p1[1]          # stable -> jointures possibles
    assert pd.isna(p1[3])                              # valeur vide -> reste vide
    assert "C001" not in p1[0]
    monkeypatch.setenv("RGPD_CLE_PSEUDO", "autre-cle")
    assert pseudonymiser(s, prefixe="CLI")[0] != p1[0]   # sans la bonne clé, pas de correspondance


def test_pseudonymisation_refuse_de_tourner_sans_cle(monkeypatch):
    monkeypatch.delenv("RGPD_CLE_PSEUDO")
    with pytest.raises(RuntimeError, match="RGPD_CLE_PSEUDO"):
        pseudonymiser(pd.Series(["x"]))


def test_masques():
    assert masquer_email(pd.Series(["jean.dupont@mail.fr"]))[0] == "j**********@mail.fr"
    assert masquer_telephone(pd.Series(["06 12 34 56 78"]))[0] == "06******78"


def test_generalisations():
    ages = generaliser_age(pd.Series(["1990-07-01", "1990-06-01", ""]), reference=date(2026, 6, 30))
    assert ages[:2].tolist() == ["30-39", "30-39"]
    assert pd.isna(ages[2])
    assert generaliser_code_postal(pd.Series(["86000", "1000", "97400"])).tolist() == ["86", "01", "974"]


# ---------------------------------------------------------------- k-anonymat
def test_k_anonymat_et_suppression_des_classes_rares():
    df = pd.DataFrame({"age": ["30-39"] * 6 + ["80-89"], "dep": ["86"] * 6 + ["974"]})
    assert k_anonymat.evaluer(df, ["age", "dep"], 5)["k_obtenu"] == 1
    filtre = k_anonymat.supprimer_classes_rares(df, ["age", "dep"], 5)
    assert len(filtre) == 6
    assert k_anonymat.evaluer(filtre, ["age", "dep"], 5)["conforme"]


# ---------------------------------------------------------------- bout en bout
def test_traitement_complet(tmp_path):
    res = traiter(RACINE / "data/reclamations_brut.csv",
                  RACINE / "config/politique_reclamations.yaml", tmp_path)
    sortie = pd.read_csv(res["fichier"], dtype=str)
    brut = pd.read_csv(RACINE / "data/reclamations_brut.csv", dtype=str)
    contenu = sortie.to_csv()
    # Aucun email, téléphone ni nom de famille source ne subsiste
    assert not any(e in contenu for e in brut["email"].head(200))
    assert not any(t in contenu for t in brut["telephone"].head(200))
    assert {"nom", "prenom", "email", "telephone", "numero_secu"}.isdisjoint(sortie.columns)
    assert res["k_apres"]["conforme"]
    assert (tmp_path / "fiche_traitement.md").exists()


def test_politique_incomplete_bloque_le_traitement(tmp_path):
    config = yaml.safe_load((RACINE / "config/politique_reclamations.yaml").read_text(encoding="utf-8"))
    del config["colonnes"]["email"]          # on « oublie » une colonne sensible
    chemin = tmp_path / "politique.yaml"
    chemin.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    with pytest.raises(PolitiqueIncomplete, match="email"):
        traiter(RACINE / "data/reclamations_brut.csv", chemin, tmp_path)
