"""
Test per il modulo excel_parser.
"""
from __future__ import annotations

import io

from src.excel_parser import leggi_excel


class TestLeggiExcel:
    def test_file_valido_restituisce_righe(self, excel_valido: bytes) -> None:
        righe, errori = leggi_excel(io.BytesIO(excel_valido))
        assert not errori
        assert len(righe) == 2

    def test_file_valido_primo_acquisto(self, excel_valido: bytes) -> None:
        righe, _ = leggi_excel(io.BytesIO(excel_valido))
        r = righe[0]
        assert r.operazione == "Carico"
        assert r.tipologia == "Acquisto"
        assert r.importo == 500.0
        assert r.fornitore == "Mario Rossi"
        assert r.descrizione == "Omega Seamaster"

    def test_colonne_mancanti_restituisce_errori(self, excel_colonne_mancanti: bytes) -> None:
        righe, errori = leggi_excel(io.BytesIO(excel_colonne_mancanti))
        assert errori
        assert not righe

    def test_file_non_excel_restituisce_errore(self) -> None:
        righe, errori = leggi_excel(io.BytesIO(b"not an excel file"))
        assert errori
        assert not righe

    def test_numero_riga_excel_corretto(self, excel_valido: bytes) -> None:
        righe, _ = leggi_excel(io.BytesIO(excel_valido))
        assert righe[0].riga_excel == 2  # riga 1 = header, dati da 2
        assert righe[1].riga_excel == 3
