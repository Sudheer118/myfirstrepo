from pathlib import Path
import pandas as pd
import re


# STAGE 1: Load + Concat CSV

def read_and_concat(folder: Path) -> pd.DataFrame:

    csv_files = sorted(folder.glob("*.csv"), key=lambda p: extract_year(p), reverse=True)

    if not csv_files:
        print(" No CSV files found.")
        return pd.DataFrame()

    dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, dtype=str).fillna("")
            if df.empty:
                print(f" Skipping empty: {file.name}")
                continue

            print(f" Loaded: {file.name} ({len(df)} rows)")
            dfs.append(df)

        except Exception as e:
            print(f" Error reading {file.name}: {e}")

    combined = pd.concat(dfs, ignore_index=True)

    print(combined.head())

    return combined



def extract_year(path: Path) -> int:
    match = re.search(r"(\d{4})-\d{2}", path.stem)
    return int(match.group(1)) if match else 0

def filter_unwanted_rows(df: pd.DataFrame) -> pd.DataFrame:
    mask = ~df.apply(
        lambda x: x.astype(str).str.contains("Grand Total|Record Not Found", case=False, na=False)
    ).any(axis=1)
    return df[mask]


def drop_sno_columns(df: pd.DataFrame) -> pd.DataFrame:
    df_copy = df.copy()
    cols_to_drop = [col for col in df_copy.columns if "s.no" in col.lower()]
    df_copy = df_copy.drop(columns=cols_to_drop)

    last_four = df_copy.columns[-4:]
    df_copy[last_four] = df_copy[last_four].apply(pd.to_numeric, errors="coerce").fillna(0)
    df_copy = df_copy[~(df_copy[last_four] == 0).all(axis=1)]

    return df_copy


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    new_columns = ["year","scheme","state_name","district_name","ben_num","ben_with_adhar","ben_with_mob","total_fund_transferred"]
    df_copy = df.copy()
    df_copy.columns = new_columns[:len(df_copy.columns)]
    return df_copy


def normalize_district_names(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "Y.S.R.": "Y.S.R. Kadapa",
        "Jajapur": "Jajpur",
        "Anugul": "Angul",
        "Ramanagara": "Bengaluru South",
        "Karimganj": "Sribhumi",
    }
    df["district_name"] = df["district_name"].replace(mapping)
    return df


def apply_manual_district_codes(df):
    manual_codes = {
        ("Delhi", "New Delhi"): "079",
        ("Delhi", "South West"): "084",
        ("Delhi", "West"): "085",
        ("Delhi", "South"): "083",
        ("Maharashtra", "Mumbai"): "482",
        ("Maharashtra", "Mumbai Suburban"): "483",
        ("Tamil Nadu", "Chennai"): "568",
        ("West Bengal", "Kolkata"):"315"
    }
    df["district_code"] = df.apply(lambda row: manual_codes.get((row["state_name"], row["district_name"]), row.get("district_code")), axis=1)
    return df


def apply_manual_state_codes(df):
    manual_state_codes = {
        "Delhi": "07", "Chandigarh": "04", "Karnataka": "29",
        "Tamil Nadu": "33", "Assam": "18", "Maharashtra": "27",
        "West Bengal": "19",
    }
    df["state_code"] = df["state_name"].map(manual_state_codes).fillna(df.get("state_code"))
    return df


def load_mapping(mapping_csv: Path):
    # Set the second row (index 1) as header
    df = pd.read_csv(mapping_csv, header=1, dtype=str)
    
    # Clean column names
    df.columns = df.columns.str.strip().str.replace(r"\s+", " ", regex=True)
    
    # Rename to standard column names
    df.rename(columns={
        "State Code": "state_code",
        "State Name (In English)": "state_name_lgd",
        "District Name (In English)": "district_name_lgd",
        "District Code": "district_code"
    }, inplace=True)
    
    # Keep only needed columns
    return df[["state_code", "state_name_lgd", "district_name_lgd", "district_code"]].drop_duplicates()


def merge_with_state_and_district_codes(df, mapping_df):
    df["state_name"] = df["state_name"].str.title()
    df["district_name"] = df["district_name"].str.title()

    merged = df.merge(mapping_df, left_on=["state_name","district_name"], right_on=["state_name_lgd","district_name_lgd"], how="left")
    merged.drop(columns=["state_name_lgd","district_name_lgd"], inplace=True)
    return merged


# RUN PIPELINE


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[2]
    
    raw_folder = base / "data/raw"
    mapping_csv = base / "data/external/LGD_Latest 1.csv"
    output_path = base / "data/processed/DBT_processed.csv"

    # Load + concat
    df = read_and_concat(raw_folder)

    # Apply full cleaning pipeline
    df = filter_unwanted_rows(df)
    #df = convert_to_title_case(df)
    # Convert all object columns to title case in-place
    df[df.select_dtypes(include=["object"]).columns] = df.select_dtypes(include=["object"]).apply(lambda x: x.str.title())

    df = drop_sno_columns(df)
    df = rename_columns(df)
    df = normalize_district_names(df)

    # Load mapping and merge
    mapping_df = load_mapping(mapping_csv)
    df = merge_with_state_and_district_codes(df, mapping_df)

    # Apply manual fixes
    df = apply_manual_state_codes(df)
    df = apply_manual_district_codes(df)

    # Format codes
    df["state_code"] = df["state_code"].fillna(0).astype(int).astype(str).str.zfill(2)
    df["district_code"] = df["district_code"].fillna(0).astype(int).astype(str).str.zfill(3)

    # Fix column order
    df = df[[
        "year","scheme","state_name","state_code",
        "district_name","district_code","ben_num",
        "ben_with_adhar","ben_with_mob","total_fund_transferred"
    ]]

    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"\n Processed file saved: {output_path}")
