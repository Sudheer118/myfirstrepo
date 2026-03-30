
# forest_data
## Package Information
- **Package Name**: forest_data
- **Source Name**: Ministry of Environment, Forest & Climate Change



# forest_survey
<details>
- **SKU**: forest_survey
- **Resource Name**: Forest cover
- **Data Extraction Link:** [Forest_Survey_of_India](https://fsi.nic.in/forest-report-2023)
- **Description:** This dataset shows the forest cover area for each district and state in India based on assessments by the Forest Survey of India. It includes different forest types such as very dense, moderately dense, and open forest, along with scrub land.
- **Raw Data Location:** dev-data-2/moefc-forest_survey-forest_cover-dt-yr-abc/raw
- **Interim Data Location:** dev-data-2/moefc-forest_survey-forest_cover-dt-yr-abc/interim
- **External Data Location:** dev-data-2/moefc-forest_survey-forest_cover-dt-yr-abc/external

# forest_statistics
<details>
- **SKU**: forest_statistics
- **Resource Name**: Forest Surey
- **Data Extraction Link:** [Forest_Survey_of_India](https://fsi.nic.in/forest-report-2023)
- **Description:** This dataset shows the area covered by different forest types across states in India. It also shows the percentage share of each forest type in the total mapped forest area, helping understand how forests are distributed across regions.
- **Raw Data Location:** dev-data-2/moefc-forest_survey-forest_statistics-st-yr-abc/raw
- **Interim Data Location:** dev-data-2/moefc-forest_survey-forest_statistics-st-yr-abc/interim
- **External Data Location:** dev-data-2/moefc-forest_survey-forest_statistics-st-yr-abc/external

# forest_fire
<details>
- **SKU**: forest_fires
- **Resource Name**: Forest Surey
- **Data Extraction Link:** [Forest_Survey_of_India](https://fsi.nic.in/forest-report-2023)
- **Description:** This dataset shows the number of forest fire alerts detected across districts and states in India using satellite observations. The alerts are captured through the VIIRS (Visible Infrared Imaging Radiometer Suite) sensor on the Suomi National Polar-orbiting Partnership (SNPP) satellite, helping monitor forest fire activity and identify areas with frequent fire incidents.
- **Raw Data Location:** dev-data-2/moefc-forest_survey-forest_fire-st-yr-abc/raw
- **Interim Data Location:** dev-data-2/moefc-forest_survey-forest_fire-st-yr-abc/interim
- **External Data Location:** dev-data-2/moefc-forest_survey-forest_fire-st-yr-abc/external
        

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

