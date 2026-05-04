"""
Modelli dati condivisi tra i moduli dell'applicazione.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Tipologia(str, Enum):
    ACQUISTO = "Acquisto"
    VENDITA = "Vendita"


class Operazione(str, Enum):
    CARICO = "Carico"
    SCARICO = "Scarico"


@dataclass
class RigaRegistro:
    """Rappresenta una singola riga del registro di carico/scarico Excel."""

    riga_excel: int  # numero riga nel file (1-based, escl. header)
    operazione: str
    data_registrazione: Optional[date]
    numero_documento: Optional[str]
    data_documento: Optional[date]
    data_operazione: Optional[date]
    mese: Optional[str]
    tipologia: str
    quantita: Optional[int]
    codice_articolo: Optional[str]
    fornitore: Optional[str]
    cliente: Optional[str]
    importo: Optional[float]
    descrizione: Optional[str]

    # Campi editabili/aggiuntivi nella GUI
    numero_documento_override: Optional[str] = None
    da_escludere: bool = False


@dataclass
class ValidationMessage:
    """Messaggio di validazione (errore o avviso)."""

    riga: int
    colonna: str
    messaggio: str
    bloccante: bool  # True = errore bloccante, False = avviso


@dataclass
class SezioneIvaDettaglio:
    causale_iva: str
    imponibile: float
    imposta: float


@dataclass
class SezioneContoDettaglio:
    conto: str
    imponibile_conto: float
    is_ritenuta_acconto: bool
    descrizione: str


@dataclass
class PagamentoDettaglio:
    data: date
    numero_documento: str
    conto: str
    importo: float


@dataclass
class PrimaNotaRecord:
    """Rappresenta un record completo da esportare nell'XML."""

    tipologia_documento_iva: str
    codice_cliente: str
    causale_contabile: str
    numero_documento: str
    data_documento: date
    data_registrazione: date
    numero_registro_iva: int
    numero_registro_iva_string: str
    protocollo_iva: int
    totale_documento: float
    descrizione: str
    sezione_iva: list[SezioneIvaDettaglio] = field(default_factory=list)
    sezione_conto: list[SezioneContoDettaglio] = field(default_factory=list)
    sezione_pagamento: list[PagamentoDettaglio] = field(default_factory=list)
