# European Life Science & MedTech Market Opportunity Analytics

## Project overview

This project develops a market-intelligence and business-intelligence workflow for
identifying potential commercial opportunities in the European life science,
diagnostics, and MedTech sectors.

The analysis is framed around a Life Science Company business areas and technology portfolio.
Because internal sales and customer data are not available, the project uses public
data to identify:

- European research projects aligned with laboratory automation, diagnostics,
  genomics, drug discovery, and related technologies;
- clinical trials that may indicate active research programs and demand for
  laboratory workflows, instrumentation, or automation; and
- market and strategic context reported in Tecan's annual results.

The intended output is an analytical dataset and an interactive dashboard that can
support market prioritization by organization, country, research field, project
value, and activity period.

> **Project status:** Work in progress. PDF extraction and the first data preparation
> workflows are implemented. The analytical dashboard is currently being developed.

## Business questions

The project is designed to answer questions such as:

1. Which European organizations are involved in research projects relevant?
2. Where are the strongest concentrations of relevant projects and funding?
3. Which organizations receive the largest project-level allocations?
4. Which countries, institutions, and therapeutic areas could represent potential
   commercial opportunities?

This is an opportunity-screening exercise. A match in the data is a signal for
further investigation, not a confirmed sales lead.

## Data sources

| Source | Coverage | Role in the analysis |
|---|---|---|
| Tecan annual reports and presentations | FY 2023–FY 2025 | Establish business context, segments, markets, and strategic priorities |
| [CORDIS](https://cordis.europa.eu/) project and organization datasets | Horizon 2020 (2014–2020) and Horizon Europe (2021–2027) | Identify relevant funded projects and their participating organizations |
| [Clinical Trials Information System (CTIS)](https://euclinicaltrials.eu/search-for-clinical-trials/) export | Snapshot dated 2026-06-26 | Identify relevant European clinical trials, sponsors, conditions, products, and endpoints |

The analysis currently uses a downloaded CTIS export. It does not yet retrieve
studies programmatically from ClinicalTrials.gov or the CTIS website.

## Analytical workflow

```text
Tecan reports (PDF) ──> page text and table extraction ──> strategic context

CORDIS projects ──> schema and type standardization ──> keyword filtering ──┐
                                                                         ├──> opportunity datasets
CORDIS organizations ──> project-ID filtering ──> project enrichment ─────┘

CTIS export ──> column and date cleaning ──> multi-field keyword filtering ──> trial dataset

Opportunity datasets ──> validation and metrics ──> Streamlit dashboard
```

### 1. Annual-report extraction

`Scripts/main.py` processes every PDF in `Reports/`.

- **PyMuPDF (`fitz`)** extracts text page by page.
- **pdfplumber** extracts detectable tables and retains their source page and table
  number.
- Each report produces separate `_text.json` and `_tables.json` files.
- `extracted_summary.json` consolidates all extracted report content and metadata.

The page-level JSON structure preserves traceability to the original report. Table
extraction is best-effort because financial-report layouts are not always represented
as native PDF tables.

### 2. CORDIS extraction and preparation

`Scripts/data_extraction.ipynb` contains the exploratory data engineering workflow
for the CORDIS project and organization files.

The two funding periods are processed separately because their schemas are similar
but not identical:

- Horizon 2020: 2014–2020
- Horizon Europe: 2021–2027



### 4. Clinical-trial cleaning

The  `TrialsDatabase.csv`, raw snapshot contains 10,000 records; 5,918 records remain after the
initial relevance filter. 

## Repository structure

```text
SalesAnalytics/
├── README.md
├── Reports/
│   ├── *.pdf
│   └── extracted_output/
│       ├── *_text.json
│       ├── *_tables.json
│       └── extracted_summary.json
└── Scripts/
    ├── main.py
    ├── data_extraction.ipynb
    └── data/
        ├── Reports/          # CORDIS source workbooks
        ├── data_raw/         # Raw CTIS snapshot
        └── data_final/       # Filtered analytical outputs
```

## Running the project

### Prerequisites

- Python 3.10 or newer
- Jupyter Notebook or JupyterLab

Install the packages currently used by the project:

```bash
python -m pip install pandas numpy openpyxl requests pymupdf pdfplumber \
  streamlit jupyter
```