"""
fetch_universe.py
------------------
Télécharge la liste publique et gratuite des entreprises cotées sur le
Nasdaq et le NYSE (fichiers officiels publiés par le Nasdaq Trader FTP,
gratuits et mis à jour quotidiennement) et produit un fichier CSV
"universe.csv" avec une colonne "ticker".

Ce script constitue notre "univers de départ" (~6000-8000 entreprises
US). On pourra plus tard y ajouter d'autres bourses (Euronext, LSE...)
en suivant le même principe : trouver une liste officielle gratuite et
l'ajouter au CSV.
"""

import pandas as pd
import requests
from io import StringIO

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


def _download(url: str) -> pd.DataFrame:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    # Le dernier caractère de chaque fichier est une ligne de statistiques
    # à ignorer (elle commence par "File Creation Time").
    lines = resp.text.splitlines()
    lines = [l for l in lines if not l.startswith("File Creation Time")]
    return pd.read_csv(StringIO("\n".join(lines)), sep="|")


def build_universe() -> pd.DataFrame:
    nasdaq = _download(NASDAQ_LISTED_URL)
    other = _download(OTHER_LISTED_URL)

    nasdaq = nasdaq.rename(columns={"Symbol": "ticker", "Security Name": "name"})
    other = other.rename(columns={"ACT Symbol": "ticker", "Security Name": "name"})

    # On retire les fonds/ETF et titres de test quand c'est identifiable
    nasdaq = nasdaq[nasdaq.get("Test Issue", "N") != "Y"]
    other = other[other.get("Test Issue", "N") != "Y"]
    if "ETF" in nasdaq.columns:
        nasdaq = nasdaq[nasdaq["ETF"] != "Y"]
    if "ETF" in other.columns:
        other = other[other["ETF"] != "Y"]

    universe = pd.concat([nasdaq[["ticker", "name"]], other[["ticker", "name"]]])
    universe = universe.dropna(subset=["ticker"]).drop_duplicates(subset=["ticker"])
    universe["ticker"] = universe["ticker"].str.strip()
    universe = universe[universe["ticker"].str.len() > 0]
    return universe.reset_index(drop=True)


if __name__ == "__main__":
    df = build_universe()
    df.to_csv("universe.csv", index=False)
    print(f"Univers construit : {len(df)} entreprises -> universe.csv")
