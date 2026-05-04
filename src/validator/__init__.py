"""
Modulo di validazione delle righe del registro.

Distingue tra:
- Errori bloccanti: impediscono la generazione XML
- Avvisi: segnalati ma non bloccanti
"""
from __future__ import annotations

from src.models import RigaRegistro, ValidationMessage
from src.utils import get_logger

logger = get_logger(__name__)

OPERAZIONI_VALIDE = {"Carico", "Scarico"}
TIPOLOGIE_VALIDE = {"Acquisto", "Vendita"}
MESI_VALIDI = {
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
}


def valida_righe(righe: list[RigaRegistro]) -> list[ValidationMessage]:
    """
    Valida tutte le righe e restituisce l'elenco dei messaggi di validazione.

    Args:
        righe: Lista di RigaRegistro da validare (già filtrata per soli acquisti).

    Returns:
        Lista di ValidationMessage ordinata per riga.
    """
    messaggi: list[ValidationMessage] = []

    for riga in righe:
        if riga.da_escludere:
            continue
        messaggi.extend(_valida_riga(riga))

    logger.info(
        "Validazione completata: %d messaggi (%d bloccanti, %d avvisi)",
        len(messaggi),
        sum(1 for m in messaggi if m.bloccante),
        sum(1 for m in messaggi if not m.bloccante),
    )
    return messaggi


def _valida_riga(riga: RigaRegistro) -> list[ValidationMessage]:
    """Valida una singola riga e restituisce i messaggi relativi."""
    msgs: list[ValidationMessage] = []

    def err(colonna: str, messaggio: str) -> None:
        msgs.append(ValidationMessage(riga.riga_excel, colonna, messaggio, bloccante=True))

    def warn(colonna: str, messaggio: str) -> None:
        msgs.append(ValidationMessage(riga.riga_excel, colonna, messaggio, bloccante=False))

    # Operazione
    if not riga.operazione or riga.operazione not in OPERAZIONI_VALIDE:
        err("Operazione", f"Valore non valido: '{riga.operazione}'. Atteso: Carico / Scarico")

    # Tipologia
    if not riga.tipologia or riga.tipologia not in TIPOLOGIE_VALIDE:
        err("Tipologia", f"Valore non valido: '{riga.tipologia}'. Atteso: Acquisto / Vendita")

    # Coerenza Operazione / Tipologia
    if riga.operazione == "Carico" and riga.tipologia != "Acquisto":
        err("Tipologia", "Carico deve avere Tipologia = Acquisto")
    if riga.operazione == "Scarico" and riga.tipologia != "Vendita":
        err("Tipologia", "Scarico deve avere Tipologia = Vendita")

    # Date obbligatorie
    if riga.data_documento is None:
        err("Data documento", "Campo obbligatorio mancante")
    if riga.data_registrazione is None:
        err("Data registrazione", "Campo obbligatorio mancante")

    # Data registrazione >= data documento (avviso)
    if riga.data_documento and riga.data_registrazione:
        if riga.data_registrazione < riga.data_documento:
            warn(
                "Data registrazione",
                "Data registrazione precedente alla data documento",
            )

    # Importo
    if riga.importo is None:
        err("Importo scheda", "Campo obbligatorio mancante")
    elif riga.importo <= 0:
        err("Importo scheda", f"L'importo deve essere positivo (trovato: {riga.importo})")

    # Fornitore (obbligatorio per Carico/Acquisto)
    if riga.operazione == "Carico" and not riga.fornitore:
        err("Fornitore", "Fornitore obbligatorio per le registrazioni di Carico")

    # Descrizione
    if not riga.descrizione:
        warn("Descrizione", "Descrizione mancante: verrà usato il codice articolo")

    # Codice articolo
    if not riga.codice_articolo:
        warn("Codice Articolo", "Codice articolo mancante")

    # Mese
    if riga.mese and riga.mese not in MESI_VALIDI:
        warn("Mese", f"Valore mese non riconosciuto: '{riga.mese}'")

    return msgs


def ha_errori_bloccanti(messaggi: list[ValidationMessage]) -> bool:
    """Restituisce True se ci sono errori bloccanti nella lista."""
    return any(m.bloccante for m in messaggi)
