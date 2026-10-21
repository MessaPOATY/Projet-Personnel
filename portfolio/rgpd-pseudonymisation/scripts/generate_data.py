"""
Génère un export SYNTHÉTIQUE de réclamations clients contenant des données personnelles
FICTIVES (noms, emails, téléphones, IBAN, n° de sécurité sociale) — aucune personne réelle.
Les IBAN et NIR sont aléatoires et ne passent pas les clés de contrôle officielles.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 11
DATA = Path(__file__).resolve().parents[1] / "data"

PRENOMS_F = ["Camille", "Inès", "Aïcha", "Léa", "Chloé", "Sarah", "Fatou", "Emma", "Manon", "Awa"]
PRENOMS_H = ["Lucas", "Hugo", "Nathan", "Yanis", "Mamadou", "Théo", "Louis", "Karim", "Enzo", "Jules"]
NOMS = ["Martin", "Bernard", "Diallo", "Petit", "Durand", "Leroy", "Moreau", "Simon", "Ndiaye", "Laurent"]
CP = ["86000"] * 30 + ["86100"] * 10 + ["86180"] * 8 + ["79000"] * 12 + ["37000"] * 10 + \
     ["69003"] * 12 + ["75011"] * 12 + ["33000"] * 5 + ["97400"]    # La Réunion : rare -> à risque
MOTIFS = ["Facturation erronée", "Retard de livraison", "Produit défectueux", "Résiliation non prise en compte",
          "Accueil téléphonique", "Remboursement non reçu"]
COMMENTAIRES = [
    "Client mécontent, souhaite un geste commercial.",
    "Rappeler le client au {tel} avant vendredi.",
    "Le client demande une réponse écrite à {email}.",
    "Remboursement à effectuer sur le compte {iban}.",
    "Dossier transmis au service litiges.",
    "Client très satisfait de la résolution finale.",
    "Attestation demandée, n° sécu indiqué par le client : {nir}.",
    "Aucune remarque.",
]


def ascii_min(s: str) -> str:
    return s.lower().translate(str.maketrans("àâäéèêëïîôöùûüç", "aaaeeeeiioouuuc"))


def main(n: int = 3000) -> None:
    rng = np.random.default_rng(SEED)
    lignes = []
    for i in range(1, n + 1):
        sexe = str(rng.choice(["F", "H"]))
        prenom = str(rng.choice(PRENOMS_F if sexe == "F" else PRENOMS_H))
        nom = str(rng.choice(NOMS))
        naissance = date(1945, 1, 1) + timedelta(days=int(rng.integers(0, 365 * 60)))
        tel = f"0{rng.integers(6, 8)} " + " ".join(f"{rng.integers(0, 100):02d}" for _ in range(4))
        email = f"{ascii_min(prenom)}.{ascii_min(nom)}{rng.integers(1, 999)}@exemple-mail.fr"
        iban = "FR76 " + " ".join(f"{rng.integers(0, 10_000):04d}" for _ in range(5)) + f" {rng.integers(0, 1000):03d}"
        nir = f"{1 if sexe == 'H' else 2} {naissance:%y} {naissance:%m} 86 {rng.integers(100, 999)} {rng.integers(100, 999)} {rng.integers(10, 97)}"
        ouverture = date(2026, 1, 1) + timedelta(days=int(rng.integers(0, 180)))
        lignes.append({
            "reclamation_id": f"REC{i:05d}",
            "date_reclamation": ouverture.isoformat(),
            "client_id": f"C{rng.integers(1, 2400):05d}",
            "nom": nom, "prenom": prenom, "email": email, "telephone": tel,
            "iban_remboursement": iban if rng.random() < 0.3 else "",
            "numero_secu": nir if rng.random() < 0.15 else "",
            "date_naissance": naissance.isoformat(),
            "code_postal": str(rng.choice(CP)),
            "sexe": sexe,
            "canal": str(rng.choice(["Téléphone", "Email", "Courrier", "Chat"], p=[0.5, 0.3, 0.1, 0.1])),
            "motif": str(rng.choice(MOTIFS)),
            "montant_litige": round(float(rng.lognormal(4, 1)), 2),
            "statut": str(rng.choice(["Clôturée", "En cours"], p=[0.8, 0.2])),
            "delai_traitement_j": int(rng.integers(1, 45)),
            "commentaire": str(rng.choice(COMMENTAIRES)).format(tel=tel, email=email, iban=iban, nir=nir),
        })
    DATA.mkdir(exist_ok=True)
    pd.DataFrame(lignes).to_csv(DATA / "reclamations_brut.csv", index=False)
    print(f"{n} réclamations fictives générées dans {DATA}")


if __name__ == "__main__":
    main()
