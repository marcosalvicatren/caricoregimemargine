"""
Test per il modulo validator.
"""
from __future__ import annotations

from src.validator import ha_errori_bloccanti, valida_righe


class TestValidazione:
    def test_riga_valida_nessun_errore(self, riga_valida) -> None:
        msgs = valida_righe([riga_valida])
        assert not ha_errori_bloccanti(msgs)

    def test_importo_mancante_errore_bloccante(self, riga_mancante_importo) -> None:
        msgs = valida_righe([riga_mancante_importo])
        errori = [m for m in msgs if m.bloccante and m.colonna == "Importo scheda"]
        assert errori

    def test_data_documento_mancante_errore_bloccante(self, riga_mancante_data) -> None:
        msgs = valida_righe([riga_mancante_data])
        errori = [m for m in msgs if m.bloccante and m.colonna == "Data documento"]
        assert errori

    def test_fornitore_mancante_errore_bloccante(self, riga_fornitore_mancante) -> None:
        msgs = valida_righe([riga_fornitore_mancante])
        errori = [m for m in msgs if m.bloccante and m.colonna == "Fornitore"]
        assert errori

    def test_importo_negativo_errore_bloccante(self, riga_valida) -> None:
        riga_valida.importo = -50.0
        msgs = valida_righe([riga_valida])
        assert ha_errori_bloccanti(msgs)

    def test_riga_esclusa_non_validata(self, riga_mancante_importo) -> None:
        riga_mancante_importo.da_escludere = True
        msgs = valida_righe([riga_mancante_importo])
        assert not msgs

    def test_data_registrazione_precedente_avviso(self, riga_valida) -> None:
        from datetime import date
        riga_valida.data_registrazione = date(2025, 10, 1)
        riga_valida.data_documento = date(2025, 11, 1)
        msgs = valida_righe([riga_valida])
        avvisi = [m for m in msgs if not m.bloccante and "registrazione" in m.colonna.lower()]
        assert avvisi

    def test_ha_errori_bloccanti_false_se_solo_avvisi(self, riga_valida) -> None:
        riga_valida.descrizione = None  # genera solo avviso
        msgs = valida_righe([riga_valida])
        assert not ha_errori_bloccanti(msgs)
