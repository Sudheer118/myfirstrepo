import pandas as pd
import re
from pathlib import Path

parent_folder = Path(__file__).resolve().parents[2] / "data/interim/forest cover"
output_path = Path(__file__).resolve().parents[2] / "data/processed/forest cover1"

output_path.mkdir(parents=True, exist_ok=True)

dfs = []
"""
cols = [
    "District",
    "Calculated Area by SoI",
    "Very Dense Forest",
    "Mod Dense Forest",
    "Open Forest",
    "Total Forest",
    "% of Area",
    "Change",
    "Scrub"
]
"""
cols = [
    "district",
    "calculated_area_by_soi",
    "very_dense_forest",
    "mod_dense_forest",
    "open_forest",
    "total_forest",
    "per_of_area",
    "change",
    "scrub"
]




years = sorted(parent_folder.iterdir())

for year in years:

    if not year.is_dir():
        continue

    print("\nProcessing year:", year.name)

    states = sorted(year.iterdir())

    for state in states:

        if not state.is_dir():
            continue

        for file in state.iterdir():

            if file.suffix.lower() != ".csv":
                continue

            print("Reading:", file)

            try:

                try:
                    df = pd.read_csv(file, encoding="latin1", header=None)
                except:
                    df = pd.read_csv(file, header=None)

            except Exception:
                print("Error reading:", file)
                continue
            
            # REMOVE HEADER / TOTAL / TABLE ROWS
            

            rows_to_drop = []

            for i in range(len(df)):

                row_text = " ".join(df.iloc[i].fillna("").astype(str)).lower()

                if any(word in row_text for word in [
                    "table",
                    "forest cover",
                    "district",
                    "dense",
                    "change",
                    "figure",
                    "assessment",
                    "area",
                    "total",
                    "grand total"
                ]):
                    rows_to_drop.append(i)

            if rows_to_drop:
                df = df.drop(rows_to_drop)

            df = df.reset_index(drop=True)


            # REMOVE ROWS WITH >3 EMPTY CELLS
            

            df = df.replace(r'^\s*$', pd.NA, regex=True)
            df = df[df.isna().sum(axis=1) <= 3]


            # KEEP FIRST 9 COLUMNS
            

            df = df.iloc[:, :9]

            if len(df.columns) != 9:
                continue

            df.columns = cols

            df["year"] = int(year.name)
            df["state"] = state.name

            dfs.append(df)


# COMBINE ALL DATA

if dfs:

    final_df = pd.concat(dfs, ignore_index=True)


    # DISTRICT CLEANING
    

    def clean_district(x):

        if pd.isna(x):
            return x

        x = str(x)

        # REMOVE NUMBERS LIKE Mysore1 Shimoga2
        x = re.sub(r"\d+", "", x)

        # KEEP VALID CHARACTERS
        x = re.split(r"[^A-Za-z &-]", x)[0]

        # REMOVE TRAILING MARKERS
        x = re.sub(r"\s+(T|H|TM|TH)$", "", x)

        # REMOVE STRANGE ATTACHED TEXT
        x = re.sub(r"([a-z])([A-Z].*)$", r"\1", x)

        return x.strip().title()

    final_df["district"] = final_df["district"].apply(clean_district)


    # CLEAN NUMERIC COLUMNS
    
    numeric_cols = [
        "calculated_area_by_soi",
        "very_dense_forest",
        "mod_dense_forest",
        "open_forest",
        "total_forest",
        "per_of_area",
        "change",
        "scrub"
    ]
   

    for col in numeric_cols:

        final_df[col] = (
            final_df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        final_df[col] = pd.to_numeric(final_df[col], errors="coerce")


    # REORDER COLUMNS
    final_df = final_df[
        [
            "year",
            "state",
            "district",
            "calculated_area_by_soi",
            "very_dense_forest",
            "mod_dense_forest",
            "open_forest",
            "total_forest",
            "per_of_area",
            "change",
            "scrub"
        ]
    ]      



    # SAVE FILE
    

    final_file = output_path / "forest_cover_all_years.csv"

    final_df.to_csv(final_file, index=False)

    print("\nSaved cleaned dataset:", final_file)

else:

    print("No data found.")