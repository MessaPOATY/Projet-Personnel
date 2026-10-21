"""
Tableau de bord de pilotage des délais de livraison — dossiers de transit.
Lancer :  streamlit run app.py
"""
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analyse

st.set_page_config(page_title="Pilotage des délais de livraison", page_icon="🚚", layout="wide")
BLEU, ORANGE, GRIS = "#1f5f8b", "#e07b39", "#9aa5b1"


@st.cache_data
def donnees():
    chemin = Path(__file__).parent / "data" / "dossiers_transit.csv"
    if not chemin.exists():          # 1er lancement (ex. Streamlit Community Cloud) : on génère la démo
        import runpy
        runpy.run_path(str(Path(__file__).parent / "scripts" / "generate_data.py"), run_name="__main__")
    return analyse.charger(chemin)


df_complet = donnees()

# ------------------------------------------------------------------ filtres
with st.sidebar:
    st.header("Filtres")
    debut, fin = df_complet["date_arrivee"].min().date(), df_complet["date_arrivee"].max().date()
    periode = st.date_input("Période d'arrivée", (debut, fin), min_value=debut, max_value=fin)
    clients = st.multiselect("Clients", sorted(df_complet["client"].unique()))
    destinations = st.multiselect("Destinations", sorted(df_complet["destination"].unique()))
    modes = st.multiselect("Mode de transport", sorted(df_complet["mode_transport"].unique()))
    st.caption("Données synthétiques — projet de démonstration.")

df = df_complet
if isinstance(periode, tuple) and len(periode) == 2:
    df = df[df["date_arrivee"].dt.date.between(*periode)]
for colonne, choix in [("client", clients), ("destination", destinations), ("mode_transport", modes)]:
    if choix:
        df = df[df[colonne].isin(choix)]

st.title("🚚 Pilotage des délais de livraison")
st.caption(f"{len(df)} dossiers de transit · de l'arrivée au port à la livraison client")

if df.empty:
    st.warning("Aucun dossier ne correspond aux filtres.")
    st.stop()

# ------------------------------------------------------------------ KPI
k = analyse.indicateurs(df)
ref = analyse.indicateurs(df_complet)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Dossiers", f"{k['dossiers']:,}".replace(",", " "))
filtre_actif = len(df) < len(df_complet)   # la comparaison au global n'a de sens que si on a filtré
c2.metric("Délai moyen", f"{k['delai_moyen']} j",
          f"{k['delai_moyen'] - ref['delai_moyen']:+.1f} j vs global" if filtre_actif else None, delta_color="inverse")
c3.metric("Taux de retard", f"{k['taux_retard']} %",
          f"{k['taux_retard'] - ref['taux_retard']:+.1f} pts vs global" if filtre_actif else None, delta_color="inverse")
c4.metric("Retard moyen (dossiers en retard)", f"{k['retard_moyen']} j")

# ------------------------------------------------------------------ évolution + goulot
gauche, droite = st.columns([3, 2])
with gauche:
    st.subheader("Évolution mensuelle")
    evo = analyse.evolution_mensuelle(df)
    fig = go.Figure()
    fig.add_bar(x=evo["mois"], y=evo["dossiers"], name="Dossiers", marker_color=GRIS, yaxis="y2", opacity=0.5)
    fig.add_scatter(x=evo["mois"], y=evo["taux_retard"], name="Taux de retard (%)",
                    mode="lines+markers", line=dict(color=ORANGE, width=3))
    fig.update_layout(height=360, margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.1),
                      yaxis=dict(title="Taux de retard (%)", rangemode="tozero"),
                      yaxis2=dict(title="Dossiers", overlaying="y", side="right", showgrid=False))
    st.plotly_chart(fig, use_container_width=True)

with droite:
    st.subheader("Où se perd le temps ?")
    etapes = analyse.decomposition_etapes(df)
    fig = px.bar(etapes.reset_index().melt(id_vars="index", value_vars=["À l'heure", "En retard"]),
                 x="value", y="index", color="statut", barmode="group", orientation="h",
                 color_discrete_map={"À l'heure": BLEU, "En retard": ORANGE},
                 labels={"value": "Durée moyenne (jours)", "index": "", "statut": ""})
    fig.update_layout(height=360, margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.1))
    fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(analyse.ETAPES.values())))
    st.plotly_chart(fig, use_container_width=True)
    if "Écart (j)" in etapes:
        goulot = etapes["Écart (j)"].idxmax()
        st.info(f"**Goulot d'étranglement : {goulot.lower()}** "
                f"(+{etapes.loc[goulot, 'Écart (j)']} j pour les dossiers en retard)")

# ------------------------------------------------------------------ Pareto + comparatif
gauche, droite = st.columns(2)
with gauche:
    st.subheader("Causes de retard (Pareto)")
    p = analyse.pareto_causes(df)
    fig = go.Figure()
    fig.add_bar(x=p["cause"], y=p["jours_perdus"], name="Jours de retard", marker_color=BLEU)
    fig.add_scatter(x=p["cause"], y=p["cumul_pct"], name="% cumulé", yaxis="y2",
                    mode="lines+markers", line=dict(color=ORANGE))
    fig.update_layout(height=380, margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.12),
                      yaxis=dict(title="Jours de retard cumulés"),
                      yaxis2=dict(title="% cumulé", overlaying="y", side="right", range=[0, 105], showgrid=False))
    st.plotly_chart(fig, use_container_width=True)

with droite:
    st.subheader("Comparatif")
    dimension = st.radio("Comparer par", ["destination", "type_marchandise", "client", "mode_transport"],
                         horizontal=True, format_func=lambda d: d.replace("_", " ").capitalize())
    comp = analyse.comparatif(df, dimension)
    st.dataframe(comp, hide_index=True, use_container_width=True, column_config={
        "taux_retard": st.column_config.ProgressColumn("Taux de retard (%)", min_value=0, max_value=100, format="%.1f"),
        "delai_moyen": st.column_config.NumberColumn("Délai moyen (j)"),
        "delai_douane": st.column_config.NumberColumn("Dédouanement (j)"),
    })

# ------------------------------------------------------------------ détail
st.subheader("Dossiers en retard")
retards = df[df["en_retard"]].sort_values("retard_j", ascending=False)[
    ["dossier_id", "client", "destination", "type_marchandise", "date_arrivee",
     "date_livraison_prevue", "date_livraison", "retard_j", "cause_retard_declaree"]].copy()
for col in ["date_arrivee", "date_livraison_prevue", "date_livraison"]:
    retards[col] = retards[col].dt.date
st.dataframe(retards, hide_index=True, use_container_width=True, height=300)
st.download_button("📥 Exporter la liste (CSV)", retards.to_csv(index=False).encode("utf-8-sig"),
                   "dossiers_en_retard.csv", "text/csv")
