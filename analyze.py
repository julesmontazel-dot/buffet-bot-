"""
analyze.py
----------
Coeur de l'application : chaque jour, ce script

1. lit l'univers d'entreprises (universe.csv),
2. sélectionne un lot d'entreprises "à contrôler aujourd'hui"
   (jamais analysées, ou dont le contrôle périodique est échu),
3. pour chacune : récupère le cours, le nombre d'actions émises et les
   capitaux propres (valeur nette comptable),
4. applique la règle : Capitalisation < Valeur nette => POSITIF,
5. écrit le résultat dans le Google Sheet,
6. sauvegarde un résumé du jour (resultats_du_jour.json) pour que
   notify.py puisse envoyer la notification Telegram.

Règle appliquée (méthode Graham/Buffett décrite par l'utilisateur) :
    Capitalisation boursière = Cours de l'action x Nombre d'actions émises
    Valeur nette = Capitaux propres de l'entreprise (Total Stockholder Equity)
    Si Capitalisation < Valeur nette -> analyse POSITIVE (marge de sécurité)
    Sinon -> analyse NEGATIVE (mais on informe quand même l'utilisateur)
"""

import json
import time
from datetime import date

import pandas as pd
import yfinance as yf

from sheets_client import (
    get_worksheet,
    load_tracked,
    upsert_result,
    is_due_for_check,
    next_check_date,
)

# Nombre max d'entreprises traitées par jour (pour rester dans les
# limites gratuites de Yahoo Finance et le temps d'exécution GitHub
# Actions). Ajustable.
BATCH_SIZE = 300
PAUSE_BETWEEN_REQUESTS = 0.3  # secondes, pour ne pas se faire bloquer


def analyze_ticker(ticker: str) -> dict | None:
    """Retourne un dict de résultat pour un ticker, ou None si les
    données nécessaires ne sont pas disponibles (entreprise à ignorer)."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        shares = info.get("sharesOutstanding")
        equity = info.get("bookValue")  # valeur comptable par action (fallback)

        # On privilégie les capitaux propres totaux issus du bilan,
        # plus fiables que "bookValue" par action.
        net_worth = None
        try:
            bs = t.balance_sheet
            if bs is not None and "Total Stockholder Equity" in bs.index:
                net_worth = float(bs.loc["Total Stockholder Equity"].iloc[0])
            elif bs is not None and "Stockholders Equity" in bs.index:
                net_worth = float(bs.loc["Stockholders Equity"].iloc[0])
        except Exception:
            pass

        if net_worth is None and equity is not None and shares is not None:
            net_worth = equity * shares  # fallback approximatif

        if price is None or shares is None or net_worth is None:
            return None  # données insuffisantes, on ignore proprement

        market_cap = price * shares
        margin_pct = round((net_worth - market_cap) / market_cap * 100, 2) if market_cap else 0
        positive = market_cap < net_worth

        return {
            "Ticker": ticker,
            "Nom": info.get("shortName", ticker),
            "Derniere_analyse": date.today().isoformat(),
            "Cours": round(price, 2),
            "Actions_emises": int(shares),
            "Capitalisation": round(market_cap, 0),
            "Valeur_nette": round(net_worth, 0),
            "Marge_securite_%": margin_pct,
            "Resultat": "POSITIF" if positive else "NEGATIF",
            "Prochain_controle": next_check_date(),
        }
    except Exception as e:
        print(f"  -> erreur sur {ticker}: {e}")
        return None


def main():
    universe = pd.read_csv("universe.csv")
    ws = get_worksheet()
    tracked = load_tracked(ws)

    # Actions émises connues précédemment, pour détecter un changement
    # (nouvelle émission d'actions) même hors période de recontrôle.
    known_shares = {
        tk: row.get("Actions_emises") for tk, row in tracked.items()
    }

    # Sélection du lot du jour : priorité aux entreprises jamais vues,
    # puis à celles dont le contrôle périodique est échu.
    never_seen = [t for t in universe["ticker"] if t not in tracked]
    due_recheck = [t for t in tracked if is_due_for_check(tracked[t])]

    today_batch = (never_seen + due_recheck)[:BATCH_SIZE]
    print(f"Entreprises à analyser aujourd'hui : {len(today_batch)}")

    resultats_du_jour = []
    for i, ticker in enumerate(today_batch, 1):
        result = analyze_ticker(ticker)
        time.sleep(PAUSE_BETWEEN_REQUESTS)
        if result is None:
            continue

        ancien_shares = known_shares.get(ticker)
        nouvelle_emission = (
            ancien_shares not in (None, "", result["Actions_emises"])
        )
        if nouvelle_emission:
            result["Nom"] += " (nouvelle émission détectée)"

        upsert_result(ws, tracked, result)
        resultats_du_jour.append(result)

        if i % 50 == 0:
            print(f"  ... {i}/{len(today_batch)} traités")

    with open("resultats_du_jour.json", "w", encoding="utf-8") as f:
        json.dump(resultats_du_jour, f, ensure_ascii=False, indent=2)

    print(f"Terminé : {len(resultats_du_jour)} entreprises analysées avec succès.")


if __name__ == "__main__":
    main()
