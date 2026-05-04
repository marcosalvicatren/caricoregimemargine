# OVWatches – Import Acquisti Orologi Usati

Applicazione Streamlit per l'importazione nella contabilità IVA/regime del margine  
degli acquisti di orologi usati da privati.

Legge un file Excel (registro carico/scarico), mostra una preview modificabile  
e genera un file XML conforme al tracciato del gestionale contabile (PrimaNotaXsd).

---

## Struttura del progetto

```
ovwatches/
├── app.py                    # Interfaccia Streamlit (entry point)
├── requirements.txt
├── README.md
├── .gitignore
├── src/
│   ├── models.py             # Dataclass condivisi
│   ├── excel_parser/         # Lettura e parsing del file Excel
│   ├── validator/            # Validazione dati (errori bloccanti e avvisi)
│   ├── mapper/               # Mapping Excel → PrimaNotaRecord
│   ├── xml_generator/        # Generazione XML conforme allo schema
│   └── utils/                # Logging centralizzato
├── tests/
│   ├── conftest.py           # Fixtures condivise
│   ├── test_excel_parser.py
│   ├── test_validator.py
│   ├── test_mapper.py
│   └── test_xml_generator.py
└── sample_data/              # File di esempio (xlsx)
```

---

## Installazione locale

### Prerequisiti
- Python 3.11 o superiore
- Git

### Passi

```bash
# 1. Clona il repository
git clone https://github.com/TUO-UTENTE/ovwatches.git
cd ovwatches

# 2. Crea un ambiente virtuale
python -m venv .venv

# 3. Attivalo
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 4. Installa le dipendenze
pip install -r requirements.txt

# 5. Avvia l'applicazione
streamlit run app.py
```

L'app si aprirà automaticamente nel browser all'indirizzo `http://localhost:8501`.

---

## Esecuzione dei test

```bash
# Dalla cartella radice del progetto, con l'ambiente virtuale attivo:
pytest tests/ -v
```

---

## Deploy su Streamlit Community Cloud

1. Fai il push del repository su **GitHub** (deve essere pubblico o privato con accesso).
2. Vai su [share.streamlit.io](https://share.streamlit.io) e accedi con il tuo account GitHub.
3. Clicca **New app**.
4. Seleziona il repository, il branch (`main`) e il file principale (`app.py`).
5. Clicca **Deploy** e attendi che l'app si avvii (circa 2–3 minuti la prima volta).

> **Nota:** Non è necessaria alcuna configurazione aggiuntiva (secrets, variabili d'ambiente).  
> L'app non richiede autenticazione e non tratta dati sensibili.

---

## Utilizzo dell'applicazione

1. **Carica il file Excel** – formato atteso: foglio `carico e scarico` con le colonne standard.
2. **Imposta la numerazione** – inserisci il protocollo IVA e il numero documento di partenza.
3. **Verifica e modifica** – nella tabella puoi:
   - Escludere righe (deseleziona "Includi") — utile per acquisti da società/P.IVA
   - Modificare importo, descrizione, data documento e numero documento
4. **Controlla la validazione** – gli errori bloccanti impediscono l'export; gli avvisi sono informativi.
5. **Scarica il file XML** – clicca il bottone per scaricare il file da importare nel gestionale.

---

## Regole di mapping (regime del margine – acquisti da privati)

| Campo XML | Valore |
|---|---|
| TipologiaDocumentoIva | `Acquisto` |
| CodiceCliente (fornitore) | `41003` |
| CausaleContabile | `FA07` |
| CausaleIva | `36M` |
| NumeroRegistroIva | `4` |
| Imposta | `0.00` (regime del margine) |
| Conto Avere | `41003` (importo negativo) |
| Conto Dare | `60101` (importo positivo) |

---

## Note per i collaboratori

- Le **vendite** (Scarico) nel file Excel vengono ignorate automaticamente.
- Le righe con **fornitore mancante** generano un errore bloccante.
- I **protocolli IVA** e i **numeri documento** sono progressivi a partire dal valore impostato.
- Se una riga ha già un numero documento nel file Excel, viene usato quello (ma è modificabile).
