"""
Modulo di mapping: converte RigaRegistro → PrimaNotaRecord.

Regole fisse per acquisti da privati (regime del margine):
  - Tipologia documento IVA : Acquisto
  - Codice fornitore        : 41003
  - Causale contabile       : FA07
  - Causale IVA             : 36M
  - Numero registro IVA     : 4
  - Imposta                 : 0 (regime del margine)
  - Sezione Conto:
      Avere  41003  –importo
      Dare   60101  +importo
      (il gestionale aggiunge in automatico 45041 con importo 0, non incluso)
"""
from __future__ import annotations

from src.models import (
    PagamentoDettaglio,
    PrimaNotaRecord,
    RigaRegistro,
    SezioneContoDettaglio,
    SezioneIvaDettaglio,
)
from src.utils import get_logger

logger = get_logger(__name__)

# Costanti contabili
CODICE_FORNITORE = "41003"
CAUSALE_CONTABILE = "FA07"
CAUSALE_IVA = "X2"
NUMERO_REGISTRO_IVA = 4
NUMERO_REGISTRO_IVA_STRING = "4"
IMPOSTA = 0.0

CONTO_FORNITORE = "41003"  # Avere
CONTO_MERCI = "60101"      # Dare


def mappa_righe(
    righe: list[RigaRegistro],
    protocollo_iniziale: int,
    numero_documento_iniziale: int,
) -> list[PrimaNotaRecord]:
    """
    Mappa le righe acquisto in record PrimaNota pronti per l'XML.

    Args:
        righe: Lista righe (filtrata solo Acquisto, non escluse).
        protocollo_iniziale: Primo protocollo IVA da usare.
        numero_documento_iniziale: Primo numero documento da usare.

    Returns:
        Lista di PrimaNotaRecord.
    """
    records: list[PrimaNotaRecord] = []
    protocollo = protocollo_iniziale
    num_doc = numero_documento_iniziale

    acquisti = [r for r in righe if not r.da_escludere and r.tipologia == "Acquisto"]

    for riga in acquisti:
        importo = riga.importo or 0.0

        # Numero documento: usa override se presente, altrimenti progressivo
        if riga.numero_documento_override:
            numero_doc_str = str(riga.numero_documento_override).strip()
        elif riga.numero_documento:
            numero_doc_str = str(riga.numero_documento).strip()
        else:
            numero_doc_str = str(num_doc)

        descrizione = riga.descrizione or f"Art. {riga.codice_articolo or '?'}"

        record = PrimaNotaRecord(
            tipologia_documento_iva="Acquisto",
            codice_cliente=CODICE_FORNITORE,
            causale_contabile=CAUSALE_CONTABILE,
            numero_documento=numero_doc_str,
            data_documento=riga.data_documento,
            data_registrazione=riga.data_registrazione,
            numero_registro_iva=NUMERO_REGISTRO_IVA,
            numero_registro_iva_string=NUMERO_REGISTRO_IVA_STRING,
            protocollo_iva=protocollo,
            totale_documento=importo,
            descrizione=descrizione,
            sezione_iva=[
                SezioneIvaDettaglio(
                    causale_iva=CAUSALE_IVA,
                    imponibile=importo,
                    imposta=IMPOSTA,
                )
            ],
            sezione_conto=[
                SezioneContoDettaglio(
                    conto=CONTO_FORNITORE,
                    imponibile_conto=-importo,  # Avere → negativo
                    is_ritenuta_acconto=False,
                    descrizione=riga.fornitore or descrizione,
                ),
                SezioneContoDettaglio(
                    conto="45041",
                    imponibile_conto=0.0,
                    is_ritenuta_acconto=False,
                    descrizione=descrizione,
                ),
                SezioneContoDettaglio(
                    conto=CONTO_MERCI,
                    imponibile_conto=importo,   # Dare → positivo
                    is_ritenuta_acconto=False,
                    descrizione=descrizione,
                ),
            ],
            sezione_pagamento=[],  # Nessun pagamento per acquisti da privati
        )

        records.append(record)
        protocollo += 1
        num_doc += 1

    logger.info("Mappati %d record PrimaNota.", len(records))
    return records
