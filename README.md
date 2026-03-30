
# ddu-gky
## Package Information
- **Package Name**: ddu-gky
- **Source Name**: Ministry of Rural Development
- **Description**: This project aims to capture and analyze the Cumulative Progress of the Deen Dayal Upadhyaya Grameen Kaushalya Yojana (DDUGKY) program. The data is sourced from the official DDUGKY Dashboard available at https://kaushalbharat.gov.in/candidateview.
 The process involves utilizing Beautiful Soup for both web scraping and data extraction, followed by data processing.The primary data source for this project is the DDUGKY Dashboard, which provides comprehensive information on the progress of the program. The data includes details such as the number of candidates trained, placed, and the overall performance metrics.

- **Data Location**: dev-data-2/mord-ddugky_detailed_report-pl-ot-fhg
- **Raw_data.py** : This file contains a script to extract the raw data.
- **district_data.py** This file contains a script to extract the district level Tc data.
- **processed_data.py** This file contains a script to process the raw data.

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

