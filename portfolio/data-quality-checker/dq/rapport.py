"""Génération des livrables : rapport HTML lisible par les métiers + export JSON pour les outils."""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from dq.moteur import Rapport


def _couleur(taux: float) -> str:
    return "#1a7f4b" if taux >= 99 else "#c27c0e" if taux >= 95 else "#c0392b"


def exporter_json(rapport: Rapport, chemin: Path) -> None:
    contenu = {
        "date_controle": datetime.now().isoformat(timespec="seconds"),
        "score_global": rapport.score_global,
        "score_par_dimension": rapport.score_par_dimension(),
        "valide": rapport.valide,
        "volumes": rapport.volumes,
        "resultats": [r.to_dict() for r in rapport.resultats],
    }
    chemin.write_text(json.dumps(contenu, ensure_ascii=False, indent=2), encoding="utf-8")


def exporter_html(rapport: Rapport, chemin: Path) -> None:
    cartes_dim = "".join(
        f'<div class="carte"><span>{d}</span><strong style="color:{_couleur(s)}">{s:.1f} %</strong></div>'
        for d, s in rapport.score_par_dimension().items()
    )
    lignes = ""
    for r in sorted(rapport.resultats, key=lambda r: (r.conforme, r.severite != "bloquant", r.taux_conformite)):
        badge = "ok" if r.conforme else ("ko" if r.severite == "bloquant" else "warn")
        libelle = "Conforme" if r.conforme else ("Bloquant" if r.severite == "bloquant" else "À surveiller")
        exemples = ", ".join(html.escape(e) for e in r.exemples) or "—"
        lignes += f"""
        <tr>
          <td><code>{r.id}</code></td><td>{r.jeu}</td><td>{html.escape(r.description)}</td>
          <td>{r.dimension}</td>
          <td class="num">{r.lignes_en_erreur} / {r.lignes_testees}</td>
          <td><div class="barre"><div style="width:{r.taux_conformite}%;background:{_couleur(r.taux_conformite)}"></div></div>
              <small>{r.taux_conformite:.2f} %</small></td>
          <td><span class="badge {badge}">{libelle}</span></td>
          <td class="ex">{exemples}</td>
        </tr>"""

    verdict = ("✅ Données validées pour publication" if rapport.valide
               else f"⛔ Publication bloquée — {len(rapport.bloquants_ko)} contrôle(s) bloquant(s) en échec")
    page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rapport qualité des données</title>
<style>
 :root {{ --fond:#f6f7f9; --carte:#fff; --texte:#1d2330; --doux:#667085; --bord:#e4e7ec; }}
 @media (prefers-color-scheme: dark) {{ :root {{ --fond:#12151c; --carte:#1b2029; --texte:#e6e8ec; --doux:#98a2b3; --bord:#2c3340; }} }}
 body {{ font-family: system-ui, sans-serif; background:var(--fond); color:var(--texte); margin:0; padding:32px 16px; }}
 main {{ max-width:1200px; margin:auto; }}
 h1 {{ margin:0 0 4px; }} .sous {{ color:var(--doux); margin-bottom:24px; }}
 .verdict {{ padding:14px 18px; border-radius:10px; background:var(--carte); border:1px solid var(--bord); margin-bottom:20px; font-weight:600; }}
 .grille {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-bottom:24px; }}
 .carte {{ background:var(--carte); border:1px solid var(--bord); border-radius:10px; padding:14px; display:flex; flex-direction:column; gap:6px; }}
 .carte span {{ color:var(--doux); font-size:13px; }} .carte strong {{ font-size:26px; }}
 .tableau {{ overflow-x:auto; background:var(--carte); border:1px solid var(--bord); border-radius:10px; }}
 table {{ border-collapse:collapse; width:100%; font-size:14px; }}
 th, td {{ padding:10px 12px; border-bottom:1px solid var(--bord); text-align:left; vertical-align:top; }}
 th {{ font-size:12px; text-transform:uppercase; color:var(--doux); }}
 code {{ white-space:nowrap; }}
 .num {{ font-variant-numeric:tabular-nums; white-space:nowrap; }}
 .barre {{ width:110px; height:8px; background:var(--bord); border-radius:4px; overflow:hidden; }}
 .barre div {{ height:100%; }}
 .badge {{ padding:3px 8px; border-radius:20px; font-size:12px; font-weight:600; white-space:nowrap; }}
 .ok {{ background:#d9f2e4; color:#1a7f4b; }} .warn {{ background:#fdf0d5; color:#8a5a00; }} .ko {{ background:#fbe0dd; color:#a12a1f; }}
 .ex {{ font-family:ui-monospace,monospace; font-size:12px; color:var(--doux); }}
</style></head><body><main>
 <h1>Rapport qualité des données</h1>
 <div class="sous">Contrôle du {datetime.now():%d/%m/%Y à %H:%M} · {sum(rapport.volumes.values())} lignes · {len(rapport.resultats)} règles</div>
 <div class="verdict">{verdict}</div>
 <div class="grille">
   <div class="carte"><span>Score global</span><strong style="color:{_couleur(rapport.score_global)}">{rapport.score_global:.1f} %</strong></div>
   {cartes_dim}
 </div>
 <div class="tableau"><table>
  <thead><tr><th>Règle</th><th>Jeu</th><th>Description</th><th>Dimension</th><th>Erreurs</th><th>Conformité</th><th>Statut</th><th>Exemples (clés)</th></tr></thead>
  <tbody>{lignes}</tbody>
 </table></div>
</main></body></html>"""
    chemin.write_text(page, encoding="utf-8")
