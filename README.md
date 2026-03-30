
# e-NAM
## Package Information
- **Package Name**: Trde_Details
- **Source Name**: Ministry of Agriculture & Farmers Welfare
- **SKU**: {moafw-enam_mandis_trade_details-st-yr-abc}
- **Resource Name**: Commodity wise trade details
- **Data Extraction Link:** [e-NAM Mandis Trade Details](https://enam.gov.in/web/dashboard/trade-data)
- **Description:** This dataset contains market-wise agricultural trade information including State, APMC, Commodity, price details (minimum, modal, and maximum), arrivals, quantity traded, unit, and date. The data is available for up to 10 years.
- **Interim Data Location:** dev-data-2/moafw-enam_mandis_trade_details-st-yr-abc/data/interim
- **Processed Data Location:** dev-data-2/mmoafw-enam_mandis_trade_details-st-yr-abc/data/processed


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

