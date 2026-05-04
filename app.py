"""
OVWatches – Importazione Acquisti Orologi Usati
Applicazione Streamlit per la generazione XML da registro Excel.
"""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
import streamlit as st

from src.excel_parser import leggi_excel
from src.mapper import mappa_righe
from src.models import RigaRegistro, ValidationMessage
from src.utils import get_logger
from src.validator import ha_errori_bloccanti, valida_righe
from src.xml_generator import genera_xml

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configurazione pagina
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="OVWatches – Import Acquisti",
    page_icon="⌚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS personalizzato
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #f8f9fa; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { color: #1a1a2e; font-size: 1.7rem !important; }
    h2 { color: #16213e; font-size: 1.2rem !important; border-bottom: 2px solid #e0e0e0; padding-bottom: 4px; }
    .error-box { background: #fff0f0; border-left: 4px solid #e53935; padding: 10px 14px; border-radius: 4px; margin: 4px 0; }
    .warn-box  { background: #fffde7; border-left: 4px solid #fdd835; padding: 10px 14px; border-radius: 4px; margin: 4px 0; }
    .ok-box    { background: #f0fff4; border-left: 4px solid #43a047; padding: 10px 14px; border-radius: 4px; margin: 4px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers di stato
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "righe": [],
        "errori_struttura": [],
        "file_caricato": False,
        "protocollo_iniziale": 1,
        "num_doc_iniziale": 1,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset() -> None:
    st.session_state["righe"] = []
    st.session_state["errori_struttura"] = []
    st.session_state["file_caricato"] = False


def _solo_acquisti(righe: list[RigaRegistro]) -> list[RigaRegistro]:
    return [r for r in righe if r.tipologia == "Acquisto"]


# ---------------------------------------------------------------------------
# Rendering messaggi validazione
# ---------------------------------------------------------------------------
def _mostra_messaggi(messaggi: list[ValidationMessage]) -> None:
    errori = [m for m in messaggi if m.bloccante]
    avvisi = [m for m in messaggi if not m.bloccante]

    if errori:
        st.markdown("#### ❌ Errori bloccanti")
        for m in errori:
            st.markdown(
                f'<div class="error-box">Riga {m.riga} – <b>{m.colonna}</b>: {m.messaggio}</div>',
                unsafe_allow_html=True,
            )
    if avvisi:
        st.markdown("#### ⚠️ Avvisi")
        for m in avvisi:
            st.markdown(
                f'<div class="warn-box">Riga {m.riga} – <b>{m.colonna}</b>: {m.messaggio}</div>',
                unsafe_allow_html=True,
            )
    if not errori and not avvisi:
        st.markdown(
            '<div class="ok-box">✅ Nessun problema rilevato. Puoi procedere con l\'export XML.</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    _init_state()

    st.title("⌚ OVWatches – Import Acquisti Orologi Usati")
    st.caption("Carica il registro Excel, verifica i dati e genera il file XML per il gestionale contabile.")

    st.divider()

    # ── 1. Upload file ──────────────────────────────────────────────────────
    st.markdown("## 1 · Carica il file Excel")

    col_up, col_reset = st.columns([4, 1])
    with col_up:
        uploaded = st.file_uploader(
            "Seleziona il file .xlsx (foglio 'carico e scarico')",
            type=["xlsx"],
            label_visibility="collapsed",
        )
    with col_reset:
        if st.button("🔄 Ricomincia", use_container_width=True):
            _reset()
            st.rerun()

    if uploaded:
        bytes_data = uploaded.read()
        righe, errori_struttura = leggi_excel(io.BytesIO(bytes_data))

        if errori_struttura:
            st.session_state["errori_struttura"] = errori_struttura
            st.session_state["file_caricato"] = False
        else:
            st.session_state["righe"] = righe
            st.session_state["errori_struttura"] = []
            st.session_state["file_caricato"] = True

    if st.session_state["errori_struttura"]:
        st.error("**Errori strutturali nel file – impossibile procedere:**")
        for e in st.session_state["errori_struttura"]:
            st.markdown(f"- {e}")
        return

    if not st.session_state["file_caricato"]:
        st.info("Carica un file .xlsx per iniziare.")
        return

    righe_all: list[RigaRegistro] = st.session_state["righe"]
    acquisti = _solo_acquisti(righe_all)

    n_scarichi = len([r for r in righe_all if r.tipologia == "Vendita"])
    st.success(
        f"File caricato: **{len(righe_all)} righe totali** "
        f"({len(acquisti)} acquisti · {n_scarichi} vendite ignorati)"
    )

    st.divider()

    # ── 2. Impostazioni numerazione ─────────────────────────────────────────
    st.markdown("## 2 · Impostazioni numerazione")

    col1, col2 = st.columns(2)
    with col1:
        protocollo_iniziale = st.number_input(
            "Protocollo IVA di partenza",
            min_value=1,
            value=st.session_state["protocollo_iniziale"],
            step=1,
            help="Il primo protocollo IVA sarà questo valore; i successivi sono progressivi.",
        )
        st.session_state["protocollo_iniziale"] = int(protocollo_iniziale)
    with col2:
        num_doc_iniziale = st.number_input(
            "Numero documento di partenza",
            min_value=1,
            value=st.session_state["num_doc_iniziale"],
            step=1,
            help="Usato solo per le righe che non hanno già un numero documento.",
        )
        st.session_state["num_doc_iniziale"] = int(num_doc_iniziale)

    st.divider()

    # ── 3. Preview e modifica righe ─────────────────────────────────────────
    st.markdown("## 3 · Anteprima e modifica acquisti")

    if not acquisti:
        st.warning("Nessuna riga di tipo 'Acquisto' trovata nel file.")
        return

    st.caption(
        "Deseleziona la casella **Includi** per escludere una riga dall'export. "
        "Puoi modificare numero documento, importo e descrizione direttamente nella tabella."
    )

    # Costruisci DataFrame per data_editor
    rows_dict = []
    for r in acquisti:
        rows_dict.append(
            {
                "riga_excel": r.riga_excel,
                "Includi": not r.da_escludere,
                "Data doc.": r.data_documento,
                "N° documento": r.numero_documento_override or r.numero_documento or "",
                "Fornitore": r.fornitore or "",
                "Importo (€)": r.importo if r.importo is not None else 0.0,
                "Descrizione": r.descrizione or "",
                "Codice art.": r.codice_articolo or "",
                "Mese": r.mese or "",
            }
        )

    df_edit = pd.DataFrame(rows_dict)

    edited = st.data_editor(
        df_edit,
        use_container_width=True,
        hide_index=True,
        disabled=["riga_excel", "Fornitore", "Codice art.", "Mese"],
        column_config={
            "riga_excel": st.column_config.NumberColumn("Riga", width="small"),
            "Includi": st.column_config.CheckboxColumn("Includi", width="small"),
            "Data doc.": st.column_config.DateColumn("Data doc.", format="DD/MM/YYYY"),
            "N° documento": st.column_config.TextColumn("N° documento"),
            "Fornitore": st.column_config.TextColumn("Fornitore"),
            "Importo (€)": st.column_config.NumberColumn("Importo (€)", format="€ %.2f", min_value=0.01),
            "Descrizione": st.column_config.TextColumn("Descrizione", width="large"),
            "Codice art.": st.column_config.TextColumn("Cod. art."),
            "Mese": st.column_config.TextColumn("Mese"),
        },
        num_rows="fixed",
        key="tabella_acquisti",
    )

    # Aggiorna il session_state con i valori modificati
    for i, riga in enumerate(acquisti):
        row = edited.iloc[i]
        riga.da_escludere = not bool(row["Includi"])
        riga.numero_documento_override = str(row["N° documento"]).strip() or None
        if row["Importo (€)"] is not None:
            riga.importo = float(row["Importo (€)"])
        if row["Descrizione"]:
            riga.descrizione = str(row["Descrizione"]).strip()
        if row["Data doc."]:
            try:
                riga.data_documento = (
                    row["Data doc."]
                    if isinstance(row["Data doc."], date)
                    else pd.to_datetime(row["Data doc."]).date()
                )
            except Exception:
                pass

    inclusi = [r for r in acquisti if not r.da_escludere]
    esclusi = len(acquisti) - len(inclusi)

    st.caption(f"**{len(inclusi)} righe incluse** · {esclusi} escluse")

    st.divider()

    # ── 4. Validazione ──────────────────────────────────────────────────────
    st.markdown("## 4 · Validazione dati")

    messaggi = valida_righe(inclusi)
    _mostra_messaggi(messaggi)

    st.divider()

    # ── 5. Export XML ───────────────────────────────────────────────────────
    st.markdown("## 5 · Esporta XML")

    bloccante = ha_errori_bloccanti(messaggi)

    if bloccante:
        st.error("❌ Correggi gli errori bloccanti prima di generare il file XML.")
    elif not inclusi:
        st.warning("Nessuna riga inclusa da esportare.")
    else:
        records = mappa_righe(
            inclusi,
            protocollo_iniziale=st.session_state["protocollo_iniziale"],
            numero_documento_iniziale=st.session_state["num_doc_iniziale"],
        )

        try:
            xml_content = genera_xml(records)

            col_btn, col_info = st.columns([2, 3])
            with col_btn:
                st.download_button(
                    label="📥 Scarica file XML",
                    data=xml_content.encode("utf-8"),
                    file_name="prima_nota_acquisti.xml",
                    mime="application/xml",
                    use_container_width=True,
                    type="primary",
                )
            with col_info:
                st.markdown(
                    f'<div class="ok-box">'
                    f'<b>{len(records)} registrazioni</b> pronte · '
                    f'Protocolli da <b>{st.session_state["protocollo_iniziale"]}</b> '
                    f'a <b>{st.session_state["protocollo_iniziale"] + len(records) - 1}</b>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with st.expander("👁 Anteprima XML (prime 80 righe)"):
                lines = xml_content.splitlines()[:80]
                st.code("\n".join(lines), language="xml")

        except Exception as e:
            st.error(f"Errore nella generazione XML: {e}")
            logger.exception("Errore generazione XML")


if __name__ == "__main__":
    main()
