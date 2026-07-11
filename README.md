# European Life Science & MedTech Market Opportunity Analytics

## Overview

An opportunity-screening dashboard for a life-science/MedTech company (lab
automation, diagnostics, genomics, drug discovery). Internal CRM/sales data
isn't available, so the project uses public EU data as a proxy instead:
[CORDIS](https://cordis.europa.eu/) (EU-funded research projects, Horizon
2020 + Horizon Europe) and [CTIS](https://euclinicaltrials.eu/search-for-clinical-trials/)
(EU clinical trials) surface which organisations, countries, and technology
areas show the strongest funded activity — and which of those best match
the company's core business. These are opportunity signals, not confirmed
sales leads.

## Data & pipeline

Two notebooks build the data the dashboard reads, run in this order:

1. **`Scripts/data_extraction.ipynb`** — loads the raw CORDIS project/
   organisation Excel exports and the raw CTIS trial CSV, keyword-filters
   both down to life-science/MedTech-relevant records, and writes
   `data/data_processed/*.csv`.
2. **`Scripts/data_cleaning.ipynb`** — standardises types, adds country
   names and ISO-3 codes (for the dashboard's choropleth maps), classifies
   each CORDIS project into a life-science category, and derives a
   deterministic High/Medium/Small opportunity tier for both CORDIS
   projects and CTIS trials. Writes the dashboard-ready CSVs to
   `data/data_clean/`.

**`Scripts/dashboard.py`** is the Streamlit app that reads those clean
CSVs, with two tabs: *CORDIS opportunities* and *Clinical trials*.
`Scripts/main.py` is a separate, one-off utility that extracts text/tables
from annual-report PDFs for business context — not part of this pipeline.

## Running locally

Requires Python 3.10+.

```bash
python -m pip install -r requirements.txt
streamlit run Scripts/dashboard.py
```

`data/data_clean/` is committed to the repo (the largest file,
`CordisDatabase_clean.csv`, is gzip-compressed to stay under GitHub's 100MB
limit), so the dashboard runs immediately — no need to re-run the notebooks
first. `requirements.txt` covers only the dashboard's runtime
(`streamlit`, `pandas`, `plotly`); re-running the notebooks also needs
`pycountry`, `babel`, `openpyxl`, `pymupdf`, `pdfplumber`, and `jupyter`.
