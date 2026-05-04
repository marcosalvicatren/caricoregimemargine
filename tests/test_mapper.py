"""
Test per il modulo mapper.
"""
from __future__ import annotations

from src.mapper import (
    CAUSALE_CONTABILE,
    CAUSALE_IVA,
    CODICE_FORNITORE,
    CONTO_FORNITORE,
    CONTO_MERCI,
    NUMERO_REGISTRO_IVA,
    mappa_righe,
)


class TestMapper:
    def test_mapping_base(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], protocollo_iniziale=1, numero_documento_iniziale=1)
        assert len(records) == 1
        r = records[0]
        assert r.tipologia_documento_iva == "Acquisto"
        assert r.codice_cliente == CODICE_FORNITORE
        assert r.causale_contabile == CAUSALE_CONTABILE
        assert r.numero_registro_iva == NUMERO_REGISTRO_IVA
        assert r.totale_documento == 500.0

    def test_protocollo_progressivo(self, riga_valida) -> None:
        from tests.conftest import _make_riga
        righe = [_make_riga(riga_excel=i) for i in range(2, 5)]
        records = mappa_righe(righe, protocollo_iniziale=10, numero_documento_iniziale=1)
        assert records[0].protocollo_iva == 10
        assert records[1].protocollo_iva == 11
        assert records[2].protocollo_iva == 12

    def test_sezione_iva_causale_e_imposta(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], 1, 1)
        det = records[0].sezione_iva[0]
        assert det.causale_iva == "X2"
        assert det.imposta == 0.0
        assert det.imponibile == 500.0

    def test_sezione_conto_due_movimenti(self, riga_valida) -> None:
        records = mappa_righe([riga_valida], 1, 1)
        conti = records[0].sezione_conto
        assert len(conti) == 2
        merci = next(c for c in conti if c.conto == CONTO_MERCI)
        iva = next(c for c in conti if c.conto == "45041")
        assert merci.imponibile_conto == 500.0
        assert iva.imponibile_conto == 0.0

    def test_riga_esclusa_non_mappata(self, riga_valida) -> None:
        riga_valida.da_escludere = True
        records = mappa_righe([riga_valida], 1, 1)
        assert not records

    def test_numero_documento_override(self, riga_valida) -> None:
        riga_valida.numero_documento_override = "MIONUM-99"
        records = mappa_righe([riga_valida], 1, 1)
        assert records[0].numero_documento == "MIONUM-99"

    def test_numero_documento_progressivo_se_assente(self, riga_valida) -> None:
        riga_valida.numero_documento = None
        riga_valida.numero_documento_override = None
        records = mappa_righe([riga_valida], protocollo_iniziale=1, numero_documento_iniziale=42)
        assert records[0].numero_documento == "42"
