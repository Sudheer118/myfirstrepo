
# plfs
## Package Information
- **Package Name**: Periodic Labour Force Survey
- **Source Name**: Ministry Of Labour And Employment

- **SKU**: {mole-plfs_annual_reports-st-yr-abc}
- **Resource Name**: Annual PLFS Reports

- **Data Extraction Link:** [PLFS-Reports](https://dge.gov.in/dge/reference-publication-reports-annual)

- **Description:** The dataset provides a comprehensive snapshot of India’s labour market outcomes across states and population groups, with a strong focus on rural and urban differentials and male/female participation. It captures how education, age, income levels, and industrial sectors shape employment patterns, earnings, and work intensity. Sourced from official DGE reference publications and annual reports.


- **Raw Data Location:** dev-data-2/mole-plfs_annual_reports-st-yr-abc/data/raw
- **Inteim Data Location:** dev-data-2/mole-plfs_annual_reports-st-yr-abc/data/interim
- **Processed Data Location:** dev-data-2/mole-plfs_annual_reports-st-yr-abc/data/processed
- **External Data Location:** dev-data-2/mole-plfs_annual_reports-st-yr-abc/data/external

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

