
# dbt
## Package Information
- **Package Name**: Direct Benefit Transfer
- **Source Name**:Ministry of Agriculture & Farmers Welfare
- **SKU**: {moafw-dbt_scheme_wise-dt-yr-abc}
- **Resource Name**: DBT Scheme wise

- **Data Extraction Link:** [DBT-Scheme wise](https://dbtdacfw.gov.in/DashboardScheme.aspx?Type=scheme)

- **Description:** The dataset explains how financial assistance under agricultural schemes is distributed to beneficiaries across districts in India. It helps assess beneficiary coverage, digital linkage, and fund flow patterns, supporting monitoring and analysis of scheme implementation and DBT performance.

- **Raw Data Location:** dev-data-2/moafw-dbt_scheme_wise-dt-yr-abc/data/raw
- **Processed Data Location:** dev-data-2/moafw-dbt_scheme_wise-dt-yr-abc/data/processed
- **External Data Location:** dev-data-2/moafw-dbt_scheme_wise-dt-yr-abc


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

