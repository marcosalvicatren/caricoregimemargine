"""
Test per il modulo xml_generator.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from src.mapper import mappa_righe
from src.xml_generator import genera_xml


def _get_records(riga_valida, n: int = 1, proto: int = 1, num_doc: int = 1):
    from tests.conftest import _make_riga
    righe = [_make_riga(riga_excel=i + 2) for i in range(n)]
    return mappa_righe(righe, protocollo_iniziale=proto, numero_documento_iniziale=num_doc)


class TestGeneraXml:
    def test_xml_valido_parseable(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], 1, 1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        assert root.tag == "PrimaNotaXsd"

    def test_xml_contiene_prima_nota(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], 1, 1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        pn = root.find(".//PrimaNotaIva")
        assert pn is not None

    def test_xml_campo_tipologia_acquisto(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], 1, 1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        tip = root.find(".//TipologiaDocumentoIva")
        assert tip is not None and tip.text == "Acquisto"

    def test_xml_causale_contabile(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], 1, 1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        caus = root.find(".//CausaleContabile")
        assert caus is not None and caus.text == "FA07"

    def test_xml_causale_iva_regime_margine(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], 1, 1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        caus_iva = root.find(".//CausaleIva")
        assert caus_iva is not None and caus_iva.text == "X2"

    def test_xml_imposta_zero(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], 1, 1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        imposta = root.find(".//Imposta")
        assert imposta is not None and float(imposta.text) == 0.0

    def test_xml_numero_record_corretto(self, riga_valida) -> None:
        from tests.conftest import _make_riga
        righe = [_make_riga(riga_excel=i + 2) for i in range(5)]
        records = mappa_righe(righe, 1, 1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        pnotes = root.findall(".//PrimaNotaIva")
        assert len(pnotes) == 5

    def test_xml_protocollo_progressivo(self, riga_valida) -> None:
        from tests.conftest import _make_riga
        righe = [_make_riga(riga_excel=i + 2) for i in range(3)]
        records = mappa_righe(righe, protocollo_iniziale=7, numero_documento_iniziale=1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        protocolli = [int(el.text) for el in root.findall(".//ProtocolloIva")]
        assert protocolli == [7, 8, 9]

    def test_xml_sezione_conto_tre_movimenti(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], 1, 1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        conti = root.findall(".//SezioneContoDettaglio")
        assert len(conti) == 3
        codici = [c.find("Conto").text for c in conti]
        assert "41003" in codici
        assert "60101" in codici
        assert "45041" in codici

    def test_xml_lista_vuota_solleva_errore(self) -> None:
        with pytest.raises(ValueError, match="Nessun record"):
            genera_xml([])

    def test_xml_data_formato_corretto(self, riga_valida) -> None:
        from datetime import date
        riga_valida.data_documento = date(2025, 11, 5)
        records = mappa_righe([riga_valida], 1, 1)
        xml_str = genera_xml(records)
        root = ET.fromstring(xml_str)
        dt = root.find(".//DataDocumento")
        assert dt is not None and dt.text == "2025-11-05"
