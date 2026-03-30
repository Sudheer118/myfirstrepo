
# agri_wages_pr
## Package Information
- **Package Name**: agriculture wages
- **Source Name**: Ministry of Agriculture & Farmers Welfare
**SKU**: {moafw-agricultural_wages-ol-mn-aji}
- **Resource Name**: agriculture wages
- **Data Extraction Link:** [Agriculural_wages](https://desagri.gov.in/document-report-category/agriculture-wages-in-india/)

- **Description:** The Agricultural wages data provided by the Ministry of Agriculture, Govt of India. It provides information on the average daily wages paid to agricultural laborers in India. The data covers different types of agricultural work, such as ploughing, sowing, harvesting, and threshing, and is broken down by state and district. The dataset also includes information on the minimum wages set by the government for different types of work for each month. The data is available for up to 10 years.

- **Raw Data Location:** dev-data-2/moafw-agricultural_wages-ol-mn-aji/data/raw
- **Interim Data Location:** dev-data-2/moafw-agricultural_wages-ol-mn-aji/data/interim
- **Pre_processed data Data Location:** dev-data-2/moafw-agricultural_wages-ol-mn-aji/data/processed
- **Processed Data Location:** dev-data-2/moafw-agricultural_wages-ol-mn-aji/data/processed

-**raw_data.py** : This file downloads the raw pdf's
-**interim.py** : This file extracts the data from pdf's
-**pre_processed.py** : This file process the data
-**processed.py** : This file maps the codes using Lgd mapping file

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

