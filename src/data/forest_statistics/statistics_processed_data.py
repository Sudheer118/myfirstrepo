
import pandas as pd
from pathlib import Path


# PATHS


parent_folder = Path(__file__).resolve().parents[2] / "data/interim/statistics"
output_path = Path(__file__).resolve().parents[2] / "data/processed/statistics"

output_path.mkdir(parents=True, exist_ok=True)

dfs = []


# LOOP THROUGH YEARS


for year in sorted(parent_folder.iterdir()):

    if not year.is_dir():
        continue

    print("\nProcessing year:", year.name)

    for state in sorted(year.iterdir()):

        if not state.is_dir():
            continue

        for file in state.glob("*.csv"):

            print("Reading:", file)

            try:
                df = pd.read_csv(file, encoding="latin1", header=None)
            except:
                df = pd.read_csv(file, header=None)


            # CHECK FIRST COLUMN FOR SL / SI
            

            first_col_text = df.iloc[:2, 0].astype(str).str.lower()

            if first_col_text.str.contains(r"\b(sl|sl no|si)\b").any():
                df = df.drop(columns=[0])


            # REMOVE HEADER ROWS
            

            mask = df.astype(str).apply(
                lambda x: x.str.contains("sl no|forest type", case=False, na=False)
            )

            df = df[~mask.any(axis=1)]

            df = df.reset_index(drop=True)


            # KEEP FIRST 3 COLUMNS MAX
            

            df = df.iloc[:, :3]


            # SET COLUMN NAMES BASED ON COUNT
            

            if df.shape[1] == 2:

                df.columns = [
                    "forest_type",
                    "total_mapped_area_per"
                ]

                df["area"] = pd.NA

            elif df.shape[1] == 3:

                df.columns = [
                    "forest_type",
                    "area",
                    "total_mapped_area_per"
                ]

            else:
                continue


            # CLEAN NUMERIC COLUMNS
            

            for col in ["area", "total_mapped_area_per"]:

                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.strip()
                )

                df[col] = pd.to_numeric(df[col], errors="coerce")


            # ADD YEAR AND STATE
            

            df["year"] = int(year.name)
            df["state"] = state.name

            dfs.append(df)


# COMBINE ALL FILES


if dfs:

    final_df = pd.concat(dfs, ignore_index=True)

    final_df = final_df[
        [
            "year",
            "state",
            "forest_type",
            "area",
            "total_mapped_area_per"
        ]
    ]

    final_file = output_path / "forest_type_all_years1.csv"

    final_df.to_csv(final_file, index=False)

    print("\nSaved cleaned dataset:", final_file)

else:
    print("No data found.")

