import pandas as pd
from pathlib import Path


def read_fire_file(file_path):
    """Read a single CSV file safely"""

    try:
        df = pd.read_csv(file_path, encoding="latin1", header=None)
    except:
        df = pd.read_csv(file_path, header=None)

    return df


def clean_fire_dataframe(df):
    """Clean dataframe and format columns"""

    # REMOVE HEADER ROWS
    mask = df.astype(str).apply(
        lambda x: x.str.contains("sl no|district", case=False, na=False)
    )
    df = df[~mask.any(axis=1)]

    # KEEP FIRST 4 COLUMNS
    df = df.iloc[:, :4]

    # SET COLUMN NAMES
    df.columns = [
        "sl_no",
        "district",
        "snpp_viirs_2022_23",
        "snpp_viirs_2023_24"
    ]

    # CLEAN NUMERIC COLUMNS
    for col in ["snpp_viirs_2022_23", "snpp_viirs_2023_24"]:

        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def process_fire_folder(parent_folder):
    """Loop through year/state folders and process all files"""

    dfs = []

    for year in sorted(parent_folder.iterdir()):

        if not year.is_dir():
            continue

        print("\nProcessing year:", year.name)

        for state in sorted(year.iterdir()):

            if not state.is_dir():
                continue

            for file in state.glob("*.csv"):

                print("Reading:", file)

                df = read_fire_file(file)

                df = clean_fire_dataframe(df)

                # ADD YEAR AND STATE
                df["year"] = int(year.name)
                df["state"] = state.name

                dfs.append(df)

    return dfs


def save_fire_dataset(dfs, output_path):
    """Combine all dataframes and save"""

    if not dfs:
        print("No data found.")
        return

    final_df = pd.concat(dfs, ignore_index=True)

    final_df = final_df[
        [
            "year",
            "state",
            "sl_no",
            "district",
            "snpp_viirs_2022_23",
            "snpp_viirs_2023_24"
        ]
    ]

    final_file = output_path / "fire_snpp_viirs_all_states.csv"

    final_df.to_csv(final_file, index=False)

    print("\nSaved cleaned dataset:", final_file)


def main():

    parent_folder = Path(__file__).resolve().parents[2] / "data/interim/fire"
    output_path = Path(__file__).resolve().parents[2] / "data/processed/fire"

    output_path.mkdir(parents=True, exist_ok=True)

    dfs = process_fire_folder(parent_folder)

    save_fire_dataset(dfs, output_path)


if __name__ == "__main__":
    main()