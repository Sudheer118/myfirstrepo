
# pmmy_mudra_loans
## Package Information

**Package Name**: Mudra Loans
- **Source Name**: Ministry of Finance
- **SKU**: {mof-mudra_reports-in-yr-abc}
- **Resource Names**: State Performance, Overall Performance, Bank Performance
- **Data Extraction Link:** [PMMY - Mudra Reports](https://www.mudra.org.in/Home/ShowPDF)
- **Description:** The PMMY performance reports present statewise, bankwise, and overall national  data on loan sanctions and disbursements over the past 10 years.

State-wise Data Location :
- **Raw Data Location:** dev-data-2/mof-mudra_state_perf-st-yr-abc/data/raw
- **Interim Data Location:** dev-data-2/mof-mudra_state_perf-st-yr-abc/data/interim
- **Processed Data Location:** dev-data-2/mof-mudra_state_perf-st-yr-abc/data/processed
- **External Data Location:** dev-data-2/mof-mudra_state_perf-st-yr-abc/data/external
- **State-wiseCodebook Location:** dev-data-2/mof-mudra_state_perf-st-yr-abc/pmmy_statewise_reports_codebook.xlsx

Overall-wise Data Location :
- **Raw Data Location:** dev-data-2/mof-mudra_overall_perf-in-yr-abc/data/raw
- **Interim Data Location:** dev-data-2/mof-mudra_overall_perf-in-yr-abc/data/interim
- **Processed Data Location:** dev-data-2/mof-mudra_overall_perf-in-yr-abc/data/processed
- **External Data Location:** dev-data-2/mof-mudra_overall_perf-in-yr-abc/data/external
- **Overall Codebook Location:**dev-data-2/mof-mudra_overall_perf-in-yr-abc/pmmy_reports_codebook.xlsx

Bank-wise Data Location :
- **Raw Data Location:** dev-data-2/mof-mudra_bank_perf-in-yr-abc/data/raw
- **Interim Data Location:** dev-data-2/mof-mudra_bank_perf-in-yr-abc/data/interim
- **Processed Data Location:** dev-data-2/mof-mudra_bank_perf-in-yr-abc/data/processed
- **External Data Location:** dev-data-2/mof-mudra_bank_perf-in-yr-abc/data/external
- **Bank Codebook Location:** dev-data-2/mof-mudra_bank_perf-in-yr-abc/pmmy_reports_codebook (1).xlsx

## Project Structure
------------
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A documentation site if available will be generated using [Docz](https://www.docz.site/)
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-mospi-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── pyproject.toml     <- Configuration file to store build system requirements for Python projects
    │
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │
    ├── features           <- Scripts to turn raw data into features for modeling
    │   └── build_features.py
    │
    ├── models             <- Scripts to train models and then use trained models to make
    │   │                 predictions
    │   ├── predict_model.py
    │   └── train_model.py
    │
    ├── visualization      <- Scripts to create exploratory and results oriented visualizations
    │   └── visualize.py
    │
    └── Dockerfile         <- Dockerfile to run the project as a container
--------

