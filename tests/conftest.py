"""
Fixtures condivise tra i test.
"""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
import pytest

from src.models import RigaRegistro


def _make_riga(
    riga_excel: int = 2,
    operazione: str = "Carico",
    tipologia: str = "Acquisto",
    data_registrazione: date | None = date(2025, 11, 10),
    data_documento: date | None = date(2025, 11, 10),
    fornitore: str | None = "Mario Rossi",
    importo: float | None = 500.0,
    descrizione: str | None = "Omega Seamaster",
    codice_articolo: str | None = "123",
    mese: str | None = "Novembre",
    numero_documento: str | None = None,
) -> RigaRegistro:
    return RigaRegistro(
        riga_excel=riga_excel,
        operazione=operazione,
        data_registrazione=data_registrazione,
        numero_documento=numero_documento,
        data_documento=data_documento,
        data_operazione=data_documento,
        mese=mese,
        tipologia=tipologia,
        quantita=1,
        codice_articolo=codice_articolo,
        fornitore=fornitore,
        cliente=None,
        importo=importo,
        descrizione=descrizione,
    )


@pytest.fixture
def riga_valida() -> RigaRegistro:
    return _make_riga()


@pytest.fixture
def riga_mancante_importo() -> RigaRegistro:
    return _make_riga(importo=None)


@pytest.fixture
def riga_mancante_data() -> RigaRegistro:
    return _make_riga(data_documento=None)


@pytest.fixture
def riga_fornitore_mancante() -> RigaRegistro:
    return _make_riga(fornitore=None)


def _build_excel_bytes(righe_dati: list[list]) -> bytes:
    """Crea un file Excel in memoria con le righe fornite."""
    header = [
        "Operazione (Clicca sul menù a tendina)",
        "Data registrazione",
        "Numero documento",
        "Data documento",
        "Data operazione",
        "Mese (Clicca sul menù a tendina)",
        "Tipologia (Clicca sul menù a tendina)",
        "Quantità",
        "Codice Articolo",
        "Fornitore",
        "Cliente",
        "Importo scheda",
        "Descrizione",
        "",
    ]
    df = pd.DataFrame([header] + righe_dati)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="carico e scarico", index=False, header=False)
        # Foglio obbligatorio
        pd.DataFrame().to_excel(writer, sheet_name="non eliminare", index=False)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def excel_valido() -> bytes:
    return _build_excel_bytes(
        [
            ["Carico", date(2025, 11, 10), None, date(2025, 11, 10),
             date(2025, 11, 10), "Novembre", "Acquisto", 1, "100",
             "Mario Rossi", "-", 500.0, "Omega Seamaster", None],
            ["Carico", date(2025, 11, 12), None, date(2025, 11, 12),
             date(2025, 11, 12), "Novembre", "Acquisto", 1, "101",
             "Luigi Bianchi", "-", 800.0, "Rolex Datejust", None],
        ]
    )


@pytest.fixture
def excel_colonne_mancanti() -> bytes:
    """File con intestazioni sbagliate."""
    df = pd.DataFrame(
        [["ColonnaA", "ColonnaB", "ColonnaC"]]
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="carico e scarico", index=False, header=False)
        pd.DataFrame().to_excel(writer, sheet_name="non eliminare", index=False)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def excel_dati_non_validi() -> bytes:
    return _build_excel_bytes(
        [
            # importo negativo
            ["Carico", date(2025, 11, 10), None, date(2025, 11, 10),
             date(2025, 11, 10), "Novembre", "Acquisto", 1, "200",
             "Mario Rossi", "-", -100.0, "Omega", None],
            # data documento mancante
            ["Carico", date(2025, 11, 10), None, None,
             date(2025, 11, 10), "Novembre", "Acquisto", 1, "201",
             "Luigi Bianchi", "-", 300.0, "Rolex", None],
        ]
    )
