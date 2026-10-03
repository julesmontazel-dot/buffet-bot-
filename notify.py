"""
notify.py
---------
Envoie une notification push via ntfy.sh résumant l'analyse du jour.
Ce message arrive simultanément sur ton iPhone (app ntfy) et sur ton
Mac (app ntfy ou navigateur sur ntfy.sh/ton-canal), dès que les deux
appareils sont abonnés au même nom de canal (NTFY_TOPIC).

Aucun compte, aucun token : le nom du canal fait office de "mot de
passe" (choisis quelque chose d'assez unique pour que personne
d'autre ne le devine).
"""

import json
import os

import requests

NTFY_URL = "https://ntfy.sh/{topic}"


def build_message(resultats: list) -> str:
    if not resultats:
        return (
            "Aucune nouvelle entreprise analysée aujourd'hui "
            "(quota atteint ou univers déjà à jour)."
        )

    positifs = [r for r in resultats if r["Resultat"] == "POSITIF"]
    negatifs = [r for r in resultats if r["Resultat"] == "NEGATIF"]

    lignes = [
        f"Entreprises analysées : {len(resultats)}",
        f"Positives : {len(positifs)}   Négatives : {len(negatifs)}",
        "",
    ]

    if positifs:
        lignes.append("Top opportunités (marge de sécurité la plus élevée) :")
        top = sorted(positifs, key=lambda r: r["Marge_securite_%"], reverse=True)[:10]
        for r in top:
            lignes.append(f"  - {r['Ticker']} ({r['Nom']}) — marge {r['Marge_securite_%']}%")

    return "\n".join(lignes)


def main():
    with open("resultats_du_jour.json", encoding="utf-8") as f:
        resultats = json.load(f)

    message = build_message(resultats)
    topic = os.environ["NTFY_TOPIC"]

    resp = requests.post(
        NTFY_URL.format(topic=topic),
        data=message.encode("utf-8"),
        headers={
            "Title": "Analyse Buffett du jour".encode("utf-8"),
            "Priority": "default",
            "Tags": "chart_with_upwards_trend",
        },
        timeout=15,
    )
    resp.raise_for_status()
    print("Notification ntfy envoyée.")


if __name__ == "__main__":
    main()
