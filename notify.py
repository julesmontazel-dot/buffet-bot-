"""
notify.py
---------
Envoie un message Telegram résumant l'analyse du jour. Ce message
arrive simultanément sur ton iPhone (app Telegram) et sur ton Mac
(app Telegram Desktop ou telegram.org/webz), puisque c'est le même
compte Telegram connecté sur les deux appareils.
"""

import json
import os

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def build_message(resultats: list) -> str:
    if not resultats:
        return (
            "📊 Analyse Buffett du jour\n\n"
            "Aucune nouvelle entreprise analysée aujourd'hui "
            "(quota atteint ou univers déjà à jour)."
        )

    positifs = [r for r in resultats if r["Resultat"] == "POSITIF"]
    negatifs = [r for r in resultats if r["Resultat"] == "NEGATIF"]

    lignes = [
        "📊 Analyse Buffett du jour",
        f"Entreprises analysées : {len(resultats)}",
        f"✅ Positives : {len(positifs)}   ❌ Négatives : {len(negatifs)}",
        "",
    ]

    if positifs:
        lignes.append("Top opportunités (marge de sécurité la plus élevée) :")
        top = sorted(positifs, key=lambda r: r["Marge_securite_%"], reverse=True)[:10]
        for r in top:
            lignes.append(f"  • {r['Ticker']} ({r['Nom']}) — marge {r['Marge_securite_%']}%")

    return "\n".join(lignes)


def main():
    with open("resultats_du_jour.json", encoding="utf-8") as f:
        resultats = json.load(f)

    message = build_message(resultats)

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    resp = requests.post(
        TELEGRAM_API.format(token=token),
        data={"chat_id": chat_id, "text": message},
        timeout=15,
    )
    resp.raise_for_status()
    print("Notification Telegram envoyée.")


if __name__ == "__main__":
    main()
