"""
Modulo per la lettura e il parsing del file Excel di registro carico/scarico.

Colonne attese (riga 0 = intestazioni, dati da riga 1):
  0  Operazione
  1  Data registrazione
  2  Numero documento
  3  Data documento
  4  Data operazione
  5  Mese
  6  Tipologia
  7  Quantità
  8  Codice Articolo
  9  Fornitore
  10 Cliente
  11 Importo scheda
  12 Descrizione
  13 (colonna vuota - ignorata)
"""
from __future__ import annotations

import io
from datetime import date
from typing import Union

import pandas as pd

from src.models import RigaRegistro
from src.utils import get_logger

logger = get_logger(__name__)

# Indici colonne
COL_OPERAZIONE = 0
COL_DATA_REGISTRAZIONE = 1
COL_NUMERO_DOCUMENTO = 2
COL_DATA_DOCUMENTO = 3
COL_DATA_OPERAZIONE = 4
COL_MESE = 5
COL_TIPOLOGIA = 6
COL_QUANTITA = 7
COL_CODICE_ARTICOLO = 8
COL_FORNITORE = 9
COL_CLIENTE = 10
COL_IMPORTO = 11
COL_DESCRIZIONE = 12

COLONNE_ATTESE = [
    "Operazione",
    "Data registrazione",
    "Numero documento",
    "Data documento",
    "Data operazione",
    "Mese",
    "Tipologia",
    "Quantità",
    "Codice Articolo",
    "Fornitore",
    "Cliente",
    "Importo scheda",
    "Descrizione",
]

SHEET_NAME = "carico e scarico"


def _parse_date(val) -> date | None:
    """Converte un valore pandas in date Python, oppure None."""
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, date):
        return val
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


def _parse_float(val) -> float | None:
    """Converte un valore in float, oppure None."""
    if pd.isna(val) or val is None or str(val).strip() in ("", "-"):
        return None
    try:
        return float(str(val).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def _parse_str(val) -> str | None:
    """Converte un valore in stringa pulita, oppure None se vuoto/dash."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return None if s in ("", "-", "nan") else s


def leggi_excel(file: Union[str, io.BytesIO]) -> tuple[list[RigaRegistro], list[str]]:
    """
    Legge il file Excel e restituisce le righe del registro e gli errori strutturali.

    Args:
        file: percorso stringa o BytesIO del file .xlsx

    Returns:
        Tupla (lista di RigaRegistro, lista di messaggi di errore strutturali).
        Gli errori strutturali sono bloccanti: se presenti, la lista righe è vuota.
    """
    errori_struttura: list[str] = []

    try:
        df = pd.read_excel(file, sheet_name=SHEET_NAME, header=None)
    except Exception as e:
        logger.error("Impossibile leggere il file Excel: %s", e)
        return [], [f"Impossibile leggere il file: {e}"]

    if df.shape[0] < 2:
        return [], ["Il foglio 'carico e scarico' è vuoto o contiene solo l'intestazione."]

    # Verifica intestazioni
    intestazioni = [str(v).strip() for v in df.iloc[0, :13].tolist()]
    for i, (attesa, trovata) in enumerate(zip(COLONNE_ATTESE, intestazioni)):
        if attesa.lower() not in trovata.lower():
            errori_struttura.append(
                f"Colonna {i+1} attesa: '{attesa}', trovata: '{trovata}'"
            )

    if errori_struttura:
        return [], errori_struttura

    dati = df.iloc[1:].reset_index(drop=True)
    righe: list[RigaRegistro] = []

    for idx, row in dati.iterrows():
        riga_excel = int(idx) + 2  # +1 per header, +1 per 1-based

        # Salta righe completamente vuote
        valori = [row[c] for c in range(13)]
        if all(pd.isna(v) or str(v).strip() in ("", "-") for v in valori):
            continue

        numero_doc_raw = _parse_str(row[COL_NUMERO_DOCUMENTO])

        riga = RigaRegistro(
            riga_excel=riga_excel,
            operazione=_parse_str(row[COL_OPERAZIONE]) or "",
            data_registrazione=_parse_date(row[COL_DATA_REGISTRAZIONE]),
            numero_documento=numero_doc_raw,
            data_documento=_parse_date(row[COL_DATA_DOCUMENTO]),
            data_operazione=_parse_date(row[COL_DATA_OPERAZIONE]),
            mese=_parse_str(row[COL_MESE]),
            tipologia=_parse_str(row[COL_TIPOLOGIA]) or "",
            quantita=int(row[COL_QUANTITA]) if not pd.isna(row[COL_QUANTITA]) else None,
            codice_articolo=_parse_str(row[COL_CODICE_ARTICOLO]),
            fornitore=_parse_str(row[COL_FORNITORE]),
            cliente=_parse_str(row[COL_CLIENTE]),
            importo=_parse_float(row[COL_IMPORTO]),
            descrizione=_parse_str(row[COL_DESCRIZIONE]),
        )
        righe.append(riga)

    logger.info("Lette %d righe dal file Excel.", len(righe))
    return righe, []
