"""Test d'intégration : le pipeline complet tourne de bout en bout sur les données générées."""
import duckdb
import pytest

from etl.pipeline import RACINE, SeuilRejetDepasse, executer


def test_chargement_bloque_si_qualite_insuffisante(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("chemins:\n  raw: data/raw\n  entrepot: data/warehouse/test_echec.duckdb\n"
                      "qualite:\n  taux_rejet_max: 0.001\n", encoding="utf-8")
    with pytest.raises(SeuilRejetDepasse):
        executer(config)
    con = duckdb.connect(str(RACINE / "data/warehouse/test_echec.duckdb"), read_only=True)
    # L'échec est tracé dans le journal, et aucune table de faits n'a été créée
    assert con.execute("SELECT statut FROM journal_executions").fetchone()[0] == "ECHEC"
    assert "fait_interactions" not in [t[0] for t in con.execute("SHOW TABLES").fetchall()]
    con.close()
    (RACINE / "data/warehouse/test_echec.duckdb").unlink()


def test_pipeline_de_bout_en_bout():
    resume = executer()
    assert resume["statut"] == "SUCCES"
    assert resume["taux_rejet"] < 0.05

    con = duckdb.connect(str(RACINE / "data/warehouse/centre_contact.duckdb"), read_only=True)
    # Intégrité référentielle : aucun fait ne pointe vers un agent inconnu
    orphelins = con.execute("""
        SELECT COUNT(*) FROM fait_interactions f
        LEFT JOIN dim_agent a USING (agent_id)
        WHERE f.agent_id IS NOT NULL AND a.agent_id IS NULL""").fetchone()[0]
    assert orphelins == 0
    # Unicité de la clé
    assert con.execute("SELECT COUNT(*) - COUNT(DISTINCT appel_id) FROM fait_interactions").fetchone()[0] == 0
    # La donnée personnelle n'a pas été chargée
    colonnes = [c[0] for c in con.execute("DESCRIBE fait_interactions").fetchall()]
    assert "numero_client" not in colonnes
    con.close()
