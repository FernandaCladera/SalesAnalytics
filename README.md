# European Life Science & MedTech Market Opportunity Analytics

## Overview

This project explores how public European data can support commercial opportunity identification for life science and MedTech companies. It combines CORDIS (EU-funded research projects) and CTIS (EU clinical trials) to identify organizations, countries, and research areas with the highest level of ongoing activity that align with the company's business. The results should be interpreted as market opportunity signals rather than confirmed sales opportunities.

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
