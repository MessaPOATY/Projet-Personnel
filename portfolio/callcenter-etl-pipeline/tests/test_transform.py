import pandas as pd
import pytest

from etl.transform import (construire_dim_date, nettoyer_appels, nettoyer_enquetes,
                           normaliser_texte, parser_dates)


def ligne(**surcharges):
    base = {"appel_id": "APL000001", "date_heure": "2026-03-02 10:15:00", "canal": "Téléphone",
            "agent_id": "AG001", "campagne_id": "CMP01", "numero_client": "0612345678",
            "duree_attente_s": "30", "duree_traitement_s": "240", "statut": "Décroché",
            "resolu_1er_contact": "Oui"}
    base.update(surcharges)
    return base


@pytest.mark.parametrize("brut, attendu", [(" Téléphone ", "telephone"), ("CHAT ", "chat"), ("E-mail", "e-mail")])
def test_normaliser_texte(brut, attendu):
    assert normaliser_texte(brut) == attendu


def test_parser_dates_formats_multiples():
    s = pd.Series(["2026-03-02 10:15:00", "02/03/2026 10:15", "2026-03-02T10:15:00", "date inconnue"])
    res = parser_dates(s)
    assert res[:3].dt.date.nunique() == 1          # les 3 formats donnent le même jour (2 mars)
    assert res[0].month == 3                        # pas d'inversion jour/mois
    assert pd.isna(res[3])


def test_variantes_de_libelles_standardisees():
    df = pd.DataFrame([ligne(appel_id="A1", canal="TEL", statut="DECROCHE", resolu_1er_contact="1"),
                       ligne(appel_id="A2", canal="mail", statut="decroche", resolu_1er_contact="FALSE")])
    propre, rejets = nettoyer_appels(df, {"AG001"})
    assert list(propre["canal"]) == ["Téléphone", "Email"]
    assert list(propre["resolu_1er_contact"]) == [True, False]
    assert rejets.empty


def test_doublons_rejetes_avec_motif():
    df = pd.DataFrame([ligne(), ligne()])
    propre, rejets = nettoyer_appels(df, {"AG001"})
    assert len(propre) == 1
    assert rejets["motif"].tolist() == ["doublon appel_id"]


@pytest.mark.parametrize("surcharge, motif", [
    ({"date_heure": "date inconnue"}, "date illisible"),
    ({"duree_traitement_s": "-12"}, "durée de traitement négative"),
    ({"agent_id": "AG999"}, "agent absent du référentiel"),
    ({"agent_id": ""}, "appel décroché sans agent"),
])
def test_regles_de_rejet(surcharge, motif):
    propre, rejets = nettoyer_appels(pd.DataFrame([ligne(**surcharge)]), {"AG001"})
    assert propre.empty
    assert rejets["motif"].iloc[0] == motif


def test_appel_abandonne_sans_agent_accepte():
    df = pd.DataFrame([ligne(agent_id="", statut="Abandonné", duree_traitement_s="0", resolu_1er_contact="")])
    propre, rejets = nettoyer_appels(df, {"AG001"})
    assert len(propre) == 1 and rejets.empty


def test_notes_csat_hors_echelle():
    df = pd.DataFrame({"appel_id": ["A1", "A2", "A3", "A4"], "note_csat": ["5", "0", "N/A", "3"]})
    propre, rejets = nettoyer_enquetes(df)
    assert propre["note_csat"].tolist() == [5, 3]
    assert len(rejets) == 2


def test_dim_date_continue():
    dim = construire_dim_date(pd.Series(pd.to_datetime(["2026-01-01 09:00", "2026-01-10 18:00"])))
    assert len(dim) == 10
    assert dim["date_key"].iloc[0] == 20260101
    assert dim.loc[dim["date_key"] == 20260103, "est_weekend"].item()   # samedi
