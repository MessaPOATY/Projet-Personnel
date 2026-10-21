import pandas as pd
import pytest

from dq.regles import CATALOGUE


@pytest.fixture
def df():
    return pd.DataFrame({
        "id": ["A", "B", "B", "D", None],
        "email": ["a.b@x.fr", "faux@", "c@d.com", "", "e@f.org"],
        "contrat": ["CDI", "cdi", "CDD", "CDI", "Stage"],
        "salaire": [30000, -5, "abc", 26000, 300000],
        "entree": ["2020-01-01", "2021-06-01", "2022-01-01", "2023-01-01", "2024-01-01"],
        "sortie": ["2021-01-01", "2021-01-01", "", "2023-06-01", ""],
        "service": ["S1", "S2", "S9", "", "S1"],
    })


def erreurs(nom, df, **params):
    return CATALOGUE[nom](df, **params).tolist()


def test_non_null(df):
    assert erreurs("non_null", df, colonne="id") == [False, False, False, False, True]


def test_unique_signale_toutes_les_occurrences(df):
    assert erreurs("unique", df, colonnes="id") == [False, True, True, False, False]


def test_valeurs_autorisees_sensible_a_la_casse(df):
    assert erreurs("valeurs_autorisees", df, colonne="contrat", valeurs=["CDI", "CDD"]) == \
        [False, True, False, False, True]


def test_intervalle_et_valeur_non_numerique(df):
    assert erreurs("intervalle", df, colonne="salaire", min=0, max=250000) == [False, True, True, False, True]


def test_format_email_ignore_les_vides(df):
    motif = r"[a-z0-9._-]+@[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}"
    assert erreurs("format", df, colonne="email", motif=motif) == [False, True, False, False, False]


def test_ordre_dates(df):
    assert erreurs("ordre_dates", df, avant="entree", apres="sortie") == [False, True, False, False, False]


def test_date_dans_le_futur():
    d = pd.DataFrame({"naissance": ["1990-05-01", "2999-01-01", "pas une date"]})
    assert erreurs("date_valide", d, colonne="naissance") == [False, True, True]


def test_cle_etrangere(df):
    ref = pd.DataFrame({"code": ["S1", "S2"]})
    assert erreurs("cle_etrangere", df, colonne="service", reference=ref, colonne_reference="code") == \
        [False, False, True, False, False]


def test_expression_metier():
    d = pd.DataFrame({"contrat": ["CDI", "Alternance", "CDI"], "salaire": [25000, 12000, 15000]})
    assert erreurs("expression", d, condition="contrat == 'Alternance' or salaire >= 21000") == [False, False, True]
