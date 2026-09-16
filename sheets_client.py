"""
sheets_client.py
-----------------
Toutes les interactions avec le Google Sheet qui sert de base de
données ET d'interface de consultation ("la rubrique" demandée).

Le Sheet doit contenir un seul onglet nommé "Suivi" avec en ligne 1
les en-têtes suivants (le script les crée automatiquement s'ils sont
absents) :

Ticker | Nom | Derniere_analyse | Cours | Actions_emises | Capitalisation |
Valeur_nette | Marge_securite_% | Resultat | Prochain_controle
"""

import json
import os
from datetime import date, datetime, timedelta

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Ticker",
    "Nom",
    "Derniere_analyse",
    "Cours",
    "Actions_emises",
    "Capitalisation",
    "Valeur_nette",
    "Marge_securite_%",
    "Resultat",
    "Prochain_controle",
]

# Nombre de jours avant de re-vérifier une entreprise déjà analysée
# (pour détecter une émission de nouvelles actions sans tout refaire
# chaque jour).
RECHECK_EVERY_DAYS = 30


def get_client() -> gspread.Client:
    creds_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_worksheet():
    client = get_client()
    sheet_id = os.environ["GOOGLE_SHEET_ID"]
    spreadsheet = client.open_by_key(sheet_id)
    try:
        ws = spreadsheet.worksheet("Suivi")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="Suivi", rows=10000, cols=len(HEADERS))
    if ws.row_values(1) != HEADERS:
        ws.update("A1", [HEADERS])
    return ws


def load_tracked(ws) -> dict:
    """Renvoie un dict {ticker: {colonne: valeur, ...}} pour toutes les
    entreprises déjà présentes dans le Sheet."""
    records = ws.get_all_records()
    return {row["Ticker"]: row for row in records}


def is_due_for_check(row: dict) -> bool:
    """Une entreprise doit être (re)contrôlée si elle n'a jamais été
    analysée, ou si la date de prochain contrôle est dépassée."""
    prochain = row.get("Prochain_controle")
    if not prochain:
        return True
    try:
        return date.fromisoformat(prochain) <= date.today()
    except ValueError:
        return True


def upsert_result(ws, tracked: dict, result: dict):
    """Insère ou met à jour la ligne correspondant à result['Ticker'].
    tracked est le dict renvoyé par load_tracked (maintenu à jour en
    mémoire pour éviter de relire le Sheet à chaque écriture)."""
    row_values = [result.get(h, "") for h in HEADERS]
    if result["Ticker"] in tracked:
        # Retrouver le numéro de ligne (les données commencent ligne 2)
        all_tickers = ws.col_values(1)
        row_idx = all_tickers.index(result["Ticker"]) + 1
        ws.update(f"A{row_idx}", [row_values])
    else:
        ws.append_row(row_values)
    tracked[result["Ticker"]] = result


def next_check_date() -> str:
    return (date.today() + timedelta(days=RECHECK_EVERY_DAYS)).isoformat()
