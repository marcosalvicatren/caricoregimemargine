"""
Modulo per la generazione del file XML conforme al tracciato PrimaNotaXsd.

Schema: SchemaImportazionePrimaNotaV2.xsd
Nessuna anagrafica esportata (acquisti da privati con codice fisso 41003).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.dom import minidom

from src.models import PrimaNotaRecord
from src.utils import get_logger

logger = get_logger(__name__)


def _fmt_date(d) -> str:
    """Formatta una date in YYYY-MM-DD."""
    return d.strftime("%Y-%m-%d") if d else ""


def _fmt_importo(v: float) -> str:
    """Formatta un importo con due decimali."""
    return f"{v:.2f}"


def _sub(parent: ET.Element, tag: str, text: str = "") -> ET.Element:
    """Crea e aggiunge un sotto-elemento con testo."""
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


def genera_xml(records: list[PrimaNotaRecord]) -> str:
    """
    Genera il contenuto XML come stringa UTF-8 formattata.

    Args:
        records: Lista di PrimaNotaRecord da serializzare.

    Returns:
        Stringa XML formattata (pretty-print).

    Raises:
        ValueError: se la lista è vuota.
    """
    if not records:
        raise ValueError("Nessun record da esportare.")

    root = ET.Element(
        "PrimaNotaXsd",
        attrib={
            "xsi:noNamespaceSchemaLocation": "SchemaImportazionePrimaNotaV2.xsd",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        },
    )

    # --- Sezione anagrafica: fornitore fisso 41003 (privati regime margine) ---
    lista_ana = ET.SubElement(root, "ListaAnagraficaClienteFornitore")
    ana = ET.SubElement(lista_ana, "AnagraficaClienteFornitore")
    dati = ET.SubElement(ana, "DatiIdentificativi")
    _sub(dati, "Codice", "41003")
    _sub(dati, "CodPaesePartitaIVa", "IT")
    _sub(dati, "PartitaIva", "")
    _sub(dati, "CodiceFiscale", "")
    _sub(dati, "Denominazione", "FORN ITA MARGINE")
    _sub(dati, "RagSocCognome", "FORN ITA MARGINE")
    _sub(dati, "Nome", "")
    sede_p = ET.SubElement(ana, "SedePrincipale")
    sede = ET.SubElement(sede_p, "Sede")
    _sub(sede, "SedeEstera", "false")
    _sub(sede, "Indirizzo", "")
    _sub(sede, "NumeroCivico", "")
    _sub(sede, "Cap", "")
    _sub(sede, "Comune", "")
    _sub(sede, "Provincia", "")
    _sub(sede, "Nazione", "Italia")
    _sub(sede, "Referente", "")
    _sub(sede, "Telefono", "")
    _sub(sede, "Telefono2", "")
    _sub(sede, "Fax", "")
    _sub(sede, "Fax2", "")
    _sub(sede, "Pec", "")
    _sub(sede, "Email", "")
    _sub(sede, "Email2", "")

    # --- Sezione prima nota ---
    lista_pn = ET.SubElement(root, "ListaPrimaNota")

    for rec in records:
        pn_imp = ET.SubElement(lista_pn, "PrimaNotaImportazione")
        pn_iva = ET.SubElement(pn_imp, "PrimaNotaIva")

        # Dati generici
        dg = ET.SubElement(pn_iva, "PrimaNotaDatiGenerici")
        _sub(dg, "TipologiaDocumentoIva", rec.tipologia_documento_iva)
        _sub(dg, "CodiceCliente", rec.codice_cliente)
        _sub(dg, "CausaleContabile", rec.causale_contabile)
        _sub(dg, "NumeroDocumento", rec.numero_documento)
        _sub(dg, "DataDocumento", _fmt_date(rec.data_documento))
        _sub(dg, "DataRegistrazione", _fmt_date(rec.data_registrazione))
        _sub(dg, "NumeroRegistroIva", str(rec.numero_registro_iva))
        _sub(dg, "NumeroRegistroIvaString", rec.numero_registro_iva_string)
        _sub(dg, "ProtocolloIva", str(rec.protocollo_iva))
        _sub(dg, "TotaleDocumento", _fmt_importo(rec.totale_documento))

        # Sezione IVA
        sez_iva = ET.SubElement(pn_iva, "PrimaNotaSezioneIva")
        lista_iva = ET.SubElement(sez_iva, "ListaDettaglioSezioneIva")
        for det in rec.sezione_iva:
            d = ET.SubElement(lista_iva, "SezioneIvaDettaglio")
            _sub(d, "CausaleIva", det.causale_iva)
            _sub(d, "Imponibile", _fmt_importo(det.imponibile))
            _sub(d, "Imposta", _fmt_importo(det.imposta))

        # Sezione Conto
        sez_conto = ET.SubElement(pn_iva, "PrimaNotaSezioneConto")
        lista_conto = ET.SubElement(sez_conto, "ListaDettaglioSezioneConto")
        for det in rec.sezione_conto:
            d = ET.SubElement(lista_conto, "SezioneContoDettaglio")
            _sub(d, "Conto", det.conto)
            _sub(d, "ImponibileConto", _fmt_importo(det.imponibile_conto))
            _sub(d, "IsRitenutaAcconto", "true" if det.is_ritenuta_acconto else "false")
            _sub(d, "Descrizione", det.descrizione)

        # Sezione Pagamento (vuota per acquisti da privati)
        sez_pag = ET.SubElement(pn_iva, "PrimaNotaSezionePagamento")
        ET.SubElement(sez_pag, "ListaPagamentoDettaglio")

    logger.info("XML generato con %d record PrimaNota.", len(records))
    return _pretty_print(root)


def _pretty_print(root: ET.Element) -> str:
    """Formatta l'albero XML in stringa indentata."""
    raw = ET.tostring(root, encoding="unicode", xml_declaration=False)
    parsed = minidom.parseString(raw)
    pretty = parsed.toprettyxml(indent="\t", encoding=None)
    # Rimuovi la riga <?xml ...?> duplicata aggiunta da minidom
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines = lines[1:]
    result = '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(lines)
    return result.rstrip() + "\n"
