from pathlib import Path

import pandas as pd
import pytest

import analyse

RACINE = Path(__file__).resolve().parents[1]


def dossier(i, arrivee, sortie_port, douane, livraison, prevue, cause=""):
    return {"dossier_id": f"D{i}", "client": "C", "mode_transport": "Maritime", "type_marchandise": "X",
            "destination": "Pointe-Noire", "poids_kg": 100,
            "date_arrivee": arrivee, "date_sortie_port": sortie_port, "date_dedouanement": douane,
            "date_livraison": livraison, "date_livraison_prevue": prevue, "cause_retard_declaree": cause}


@pytest.fixture
def df():
    brut = pd.DataFrame([
        # à l'heure : 2 j port, 3 j douane, 2 j transport = 7 j (prévu 10)
        dossier(1, "2026-01-01", "2026-01-03", "2026-01-06", "2026-01-08", "2026-01-11"),
        # en retard de 4 j à cause de la douane : 2 + 10 + 2 = 14 j
        dossier(2, "2026-01-01", "2026-01-03", "2026-01-13", "2026-01-15", "2026-01-11", "Documents incomplets"),
        # en retard de 2 j, cause non renseignée
        dossier(3, "2026-02-01", "2026-02-03", "2026-02-06", "2026-02-13", "2026-02-11"),
    ])
    for c in [c for c in brut.columns if c.startswith("date_")]:
        brut[c] = pd.to_datetime(brut[c])
    return analyse.preparer(brut)


def test_durees_par_etape(df):
    assert df[["j_port", "j_douane", "j_transport", "delai_total_j"]].iloc[1].tolist() == [2, 10, 2, 14]


def test_retard_jamais_negatif(df):
    assert df["retard_j"].tolist() == [0, 4, 2]
    assert df["en_retard"].tolist() == [False, True, True]


def test_indicateurs(df):
    k = analyse.indicateurs(df)
    assert k["dossiers"] == 3
    assert k["taux_retard"] == pytest.approx(66.7)
    assert k["retard_moyen"] == 3.0


def test_indicateurs_sur_selection_vide(df):
    assert analyse.indicateurs(df.iloc[0:0])["dossiers"] == 0


def test_goulot_identifie(df):
    etapes = analyse.decomposition_etapes(df)
    assert etapes["Écart (j)"].idxmax() == "Dédouanement"


def test_pareto_cumul_et_cause_manquante(df):
    p = analyse.pareto_causes(df)
    assert p["cause"].tolist() == ["Documents incomplets", "Non renseignée"]
    assert p["cumul_pct"].iloc[-1] == 100.0


def test_donnees_generees_coherentes():
    df = analyse.charger(RACINE / "data" / "dossiers_transit.csv")
    assert df["dossier_id"].is_unique
    assert (df[["j_port", "j_douane", "j_transport"]] >= 0).all().all()
    assert (df["date_livraison"] >= df["date_arrivee"]).all()
