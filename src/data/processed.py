
from pathlib import Path
import pandas as pd
import re
import numpy as np

# Shared Helpers

def read_csv_no_header(input_path: Path) -> pd.DataFrame:
    return pd.read_csv(input_path, header=None, dtype=str, encoding="utf-8")


def extract_year_from_filename(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2})", path.stem)
    return match.group(1) if match else "Unknown"


def sort_files_by_year_desc(files: list[Path]) -> list[Path]:
    return sorted(files, key=extract_year_from_filename, reverse=True)



# Overall-specific logic 

def remove_total_and_after(df: pd.DataFrame) -> pd.DataFrame:
    # Convert all cells to string
    df_str = df.astype(str).apply(lambda col: col.str.strip().str.lower())
    
    # Create mask of cells starting with 'total'
    mask = df_str.apply(lambda col: col.str.startswith("total"))

    if mask.any().any():
        row, col_name = mask.stack().idxmax()
        col_index = df.columns.get_loc(col_name)
        print(f"Found 'Total' at row {row}, column {col_name} — removing columns after it.")
        return df.iloc[:, :col_index]

    return df

def remove_rows_with_keywords(df: pd.DataFrame) -> pd.DataFrame:
    pattern = r"total|out of above"  # regex, case-insensitive
    # convert to string, fill NaN to avoid errors
    mask = df.fillna("").astype(str).apply(lambda col: col.str.contains(pattern, case=False, na=False))
    # keep rows where none of the columns match
    return df[~mask.any(axis=1)]



def has_loans_upto(df: pd.DataFrame) -> bool:
    pattern = re.compile(r"^\(loans\s*up\s*to\s*rs\.?\s*50,000\)$", re.IGNORECASE)
    for r in range(1, df.shape[0]):
        for c in range(df.shape[1]):
            val = str(df.iat[r, c]).strip()
            if pattern.fullmatch(val):
                return True
    return False


def combine_two_header_rows(df: pd.DataFrame, skip_top: int = 1) -> pd.DataFrame:
    df = df.iloc[skip_top:].reset_index(drop=True)
    headers = (df.iloc[0].fillna('') + ' ' + df.iloc[1].fillna('')).str.strip()
    df.columns = headers
    return df.iloc[2:].reset_index(drop=True)


def flatten_two_row_header_overall(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(df.columns[0], axis=1, errors='ignore')
    top, bottom = df.iloc[1].fillna(""), df.iloc[2].fillna("")
    combined, prefix = [], ""
    for t, b in zip(top, bottom):
        t_clean, b_clean = re.sub(r"\s+", "_", str(t).lower()), re.sub(r"\s+", "_", str(b).lower())
        if t_clean:
            prefix = t_clean
        name = prefix if not b_clean or b_clean == "nan" else f"{prefix}_{b_clean}"
        name = re.sub(r"_+", "_", name).strip("_")
        combined.append(name)
    combined[:1] = ["category"]
    df.columns = combined[:len(df.columns)]
    return df.iloc[3:].reset_index(drop=True)


def flatten_three_row_header_overall(df: pd.DataFrame) -> pd.DataFrame:
    top = pd.Series(df.columns).astype(str).str.strip()
    bottom = df.iloc[0].fillna("").astype(str).str.strip()
    headers, prefix = [], ""
    for t, b in zip(top, bottom):
        t_clean, b_clean = re.sub(r"\s+", "_", t.lower()), re.sub(r"\s+", "_", b.lower())
        if t_clean:
            prefix = t_clean
        name = prefix if not b_clean else f"{prefix}_{b_clean}"
        name = re.sub(r"_+", "_", name).strip("_")
        headers.append(name)
    df.columns = headers
    return df.iloc[1:].reset_index(drop=True)


def normalize_column_names_overall(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [
        re.sub(r"kishoer|kishor(e)?(?=(_|$))", "kishore", c, flags=re.IGNORECASE).lower()
        for c in df.columns
    ]
    return df


def clean_bracket_headers(df: pd.DataFrame) -> pd.DataFrame:
    new_cols = []
    for col in df.columns:
        c = re.sub(r"\([^)]*\)", "", str(col))
        c = re.sub(r"_+", "_", c).strip("_ ").lower()
        new_cols.append(c)
    df.columns = new_cols
    return df


def process_file_overall(input_file: Path) -> pd.DataFrame:
    print(f"Processing (Overall): {input_file.name}")

    df = read_csv_no_header(input_file)

    #  Apply string-cleaning once
    df = df.map(lambda x: str(x) if not pd.isna(x) else "")

    df = remove_total_and_after(df)
    df = remove_rows_with_keywords(df)

    if has_loans_upto(df):
        df = combine_two_header_rows(df, skip_top=1)
        df = flatten_three_row_header_overall(df)
    else:
        df = flatten_two_row_header_overall(df)

    df = df.drop(columns=["sr_no"], errors="ignore")
    df = normalize_column_names_overall(df)
    df = clean_bracket_headers(df)

    df.insert(0, "year", extract_year_from_filename(input_file))
    return df



def process_all_overall(input_dir: Path, output_dir: Path) -> None:
    all_files = list(input_dir.glob("*.csv"))
    if not all_files:
        print("No Overall CSV files found.")
        return
    sorted_files = sort_files_by_year_desc(all_files)
    print("\nOverall files to process (newest first):")
    for f in sorted_files:
        print(f"  - {f.name}")
    merged_df = pd.concat([process_file_overall(f) for f in sorted_files], ignore_index=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "Overall_processed.csv"
    merged_df.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"Overall output saved to: {out_file}   (rows: {len(merged_df)})")



# Bank-specific logic

def remove_rows_total_bank(df: pd.DataFrame) -> pd.DataFrame:
    mask = df.astype(str).apply(lambda col: col.str.contains("total", case=False, na=False))
    return df[~mask.any(axis=1)]


def flatten_two_row_header_bank(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(df.columns[0], axis=1, errors='ignore')
    top = df.iloc[1].fillna("").astype(str).str.strip()
    bottom = df.iloc[2].fillna("").astype(str).str.strip()

    combined, prefix = [], ""
    for t, b in zip(top, bottom):
        t_clean = re.sub(r"\s+", "_", t.lower().strip())
        b_clean = re.sub(r"\s+", "_", b.lower().strip())
        if t_clean:
            prefix = t_clean
        if not prefix and not b_clean:
            combined.append("")
            continue
        name = prefix if not b_clean or b_clean == "nan" else f"{prefix}_{b_clean}"
        name = re.sub(r"_+", "_", name).strip("_")
        combined.append(name)

    if "sponsor" in " ".join(top).lower():
        combined[:3] = ["bank_type", "bank_name", "sponsor_bank"]
    else:
        combined[:2] = ["bank_type", "bank_name"]

    df.columns = combined[:len(df.columns)]
    df = df.iloc[3:].reset_index(drop=True)
    return df


def simplify_column_names_bank(df: pd.DataFrame) -> pd.DataFrame:
    new_names = []
    for name in df.columns:
        name = re.sub(r"\(.*?\)", "", str(name))
        name = re.sub(r"[^\w\s]", "_", name)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_").lower()
        new_names.append(name)
    df.columns = new_names
    return df


def normalize_column_names_bank(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [
        re.sub(r"kishoer|kishor(e)?(?=(_|$))", "kishore", c, flags=re.IGNORECASE).lower()
        for c in df.columns
    ]
    return df


def fix_kishore_columns_bank(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "kishore_loans_from_rs_50_001_to_rs_5_00_no_of_a_cs": "kishore_no_of_a_cs",
        "kishore_loans_from_rs_50_001_to_rs_5_00_sanction_amt": "kishore_sanction_amt",
        "kishore_loans_from_rs_50_001_to_rs_5_00_disbursement_amt": "kishore_disbursement_amt",
    }
    existing = {k: v for k, v in rename_map.items() if k in df.columns}
    if existing:
        df = df.rename(columns=existing)
    return df


def fill_down_and_remove(df: pd.DataFrame, col_index: int) -> pd.DataFrame:
    col = df.iloc[:, col_index].replace(["", "nan", None], pd.NA)
    
    # forward fill the group column
    filled = col.ffill()

    # identify the rows that were originally group headers (non-empty before fill)
    to_remove = col.notna()

    # update df with filled values
    df.iloc[:, col_index] = filled

    # return df without the original header rows
    return df.loc[~to_remove].reset_index(drop=True)




def process_single_csv_bank(input_file: Path) -> pd.DataFrame:
    print(f"\nProcessing (Bank): {input_file.name}")
    year = extract_year_from_filename(input_file)

    df = read_csv_no_header(input_file)

    #  Apply string-cleaning once
    df = df.map(lambda x: str(x) if not pd.isna(x) else "")

    df = remove_total_and_after(df)
    df = remove_rows_total_bank(df)
    df = flatten_two_row_header_bank(df)
    df = simplify_column_names_bank(df)
    df = normalize_column_names_bank(df)
    df = fix_kishore_columns_bank(df)
    df = fill_down_and_remove(df, 0)

    df.insert(0, "year", year)
    if "sponsor_bank" in df.columns:
        df["sponsor_bank"] = df["sponsor_bank"].replace("-", np.nan)
    return df


def process_all_bank(input_dir: Path, output_dir: Path) -> None:
    all_files = list(input_dir.glob("*.csv"))
    if not all_files:
        print("No Bank CSV files found.")
        return
    sorted_files = sort_files_by_year_desc(all_files)
    print("\nBank files to process (newest first):")
    for f in sorted_files:
        print(f"  - {f.name}")
    merged = pd.concat((process_single_csv_bank(f) for f in sorted_files), ignore_index=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "BankWise_Merged.csv"
    merged.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"Bank output saved to: {out_file}   (rows: {len(merged)})")



# State-specific logic 


# Helper functions

def get_processed_headers(csv_path: Path) -> tuple[list[str], int | None]:

    # Read first 3 rows
    header_df = pd.read_csv(csv_path, nrows=3, header=None)
    second = header_df.iloc[1].fillna("").astype(str)
    third = header_df.iloc[2].fillna("").astype(str)

    # Forward-fill top-level headers for empty cells
    second_ffill = second.replace("", pd.NA).ffill().fillna("").astype(str)

    # Find cutoff index where 'Total' starts in second row
    cutoff = next((i for i, val in enumerate(second_ffill) if val.strip().startswith("Total")), None)
    if cutoff is not None:
        second_ffill = second_ffill[:cutoff]
        third = third[:cutoff]

    # Combine headers
    combined = [(f"{top} {bottom}").strip() for top, bottom in zip(second_ffill, third)]
    # Remove extra spaces
    combined = [re.sub(r"\s+", " ", col) for col in combined]

    return combined, cutoff


def merge_dadra_and_diu(df: pd.DataFrame) -> pd.DataFrame:

    # Replace the two states with a single combined name
    df['State Name'] = df['State Name'].replace({
        "Dadra and Nagar Haveli": "The Dadra and Nagar Haveli and Daman and Diu",
        "Daman and Diu": "The Dadra and Nagar Haveli and Daman and Diu"
    })

    # Identify numeric columns to sum
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # Group by state name and sum numeric columns
    df = df.groupby('State Name', as_index=False)[numeric_cols].sum()

    return df

def standardize_names(df: pd.DataFrame) -> pd.DataFrame:
    """Clean state names and column names, minimal operations."""
    # Rename columns if exist
    df = df.rename(columns={"Sr No": "id", "State Name": "state_name"})

    # Fix column names: simple replace
    df.columns = [re.sub(r"\bKishor\b", "Kishore", col, flags=re.IGNORECASE).replace(" ", "_") for col in df.columns]

    # Reorder core columns first if exist
    core = ["id", "year", "state_name"]
    cols = [c for c in core if c in df.columns] + [c for c in df.columns if c not in core]
    return df[cols]


def merge_state_codes(df: pd.DataFrame, mapping_csv: Path) -> pd.DataFrame:
    mapping_df = pd.read_csv(mapping_csv, header=1)[
        ["State Code", "State Name (In English)"]
    ].drop_duplicates()

    mapping_df.columns = ["state_code", "state_name"]
    mapping_df["state_name"] = mapping_df["state_name"].str.strip().str.title()
    mapping_df["state_code"] = mapping_df["state_code"].astype(str).str.zfill(2)

    # NORMALIZE DF SIDE
    df["state_name"] = df["state_name"].astype(str).str.strip().str.title()

    replacements = {
        "Union Territory Of Ladakh": "Ladakh",
        "Union Territory Of Jammu And Kashmir": "Jammu And Kashmir",
        "Pondicherry": "Puducherry",
    }

    df["state_name"] = df["state_name"].replace(replacements)

    df = df.merge(mapping_df, on="state_name", how="left")

    manual_codes = {"Delhi": "07", "Chandigarh": "04"}
    df["state_code"] = df["state_name"].map(manual_codes).fillna(df["state_code"])
    df["state_code"] = df["state_code"].astype(str).str.zfill(2)

    df.insert(df.columns.get_loc("state_name") + 1, "state_code", df.pop("state_code"))
    return df


def process_single_csv(csv_path: Path) -> pd.DataFrame:
    print(f"\nProcessing: {csv_path.name}")

    # Extract year once
    year = extract_year_from_filename(csv_path)

    # Prepare headers
    headers, cutoff = get_processed_headers(csv_path)

    df = pd.read_csv(csv_path, skiprows=3, header=None)

    # Limit columns up to 'Total'
    if cutoff is not None:
        df = df.iloc[:, :cutoff]

    df.columns = headers[:df.shape[1]]

    # Remove Total rows
    df = df[~df["State Name"].str.contains("Total", case=False, na=False)]

    # Process state grouping
    df = merge_dadra_and_diu(df)

    # Standard formatting
    df = standardize_names(df)

    # Insert year AFTER cleanup
    df.insert(1, "year", year)

    print(f"Done ({len(df)} rows)")
    return df



def process_all_csvs(input_folder: Path, mapping_csv: Path, output_path: Path):
    files = sorted(input_folder.glob("StateWise_Performance_*.csv"), key=extract_year_from_filename, reverse=True)
    dfs = []
    for f in files:
        try:
            dfs.append(process_single_csv(f))
        except Exception as e:
            print(f"Skipped {f.name}: {e}")
            continue

    final_df = pd.concat(dfs, ignore_index=True)
    final_df = merge_state_codes(final_df, mapping_csv)
    final_df.drop(columns="id", errors="ignore", inplace=True)
    final_df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")
 


def run_all(
    interim_root: Path = Path(__file__).resolve().parents[2] / "data/interim",
    processed_root: Path = Path(__file__).resolve().parents[2] / "data/processed",
    state_mapping_file: Path = Path(__file__).resolve().parents[2] / "data/external/LGD_Latest 1.csv"
) -> None:
    """
    Unified runner for Overall, Bank, and State data processing.
    """

    print(f"\n--- Unified PMMY Pipeline ---")
    print(f"Interim root: {interim_root}")
    print(f"Processed root: {processed_root}\n")

    # Define targets
    targets = [
        ("Overall", process_all_overall, interim_root / "Overall", processed_root / "Overall"),
        ("Bank", process_all_bank, interim_root / "Bank", processed_root / "Bank"),
        ("State", process_all_csvs, interim_root / "State", processed_root / "State"),
    ]

    for name, processor, input_dir, output_dir in targets:
        if not input_dir.exists():
            print(f"Skipping {name}: folder not found -> {input_dir}")
            continue

        print(f"\n--- Processing {name} ---")
        try:
            if name == "State":
                # Use the new State logic with mapping
                output_file = output_dir / "StateWiseProcessed.csv"
                output_dir.mkdir(parents=True, exist_ok=True)
                processor(input_dir, state_mapping_file, output_file)
            else:
                # Overall or Bank
                processor(input_dir, output_dir)
        except Exception as e:
            print(f"Error while processing {name}: {e}")

    print("\n--- Unified pipeline finished ---\n")


if __name__ == "__main__":
    run_all()
