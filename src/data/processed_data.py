from pathlib import Path
import re
import pandas as pd


# CONFIGURATIONS & CONSTANTS

BUCKET_PATTERN = re.compile(r"Age Bucket:\s*(.+)", re.IGNORECASE)
YEAR_COL_PATTERN = re.compile(r"^\d{4}-\d{2}(?:\s*\(.*\))?$")
MONTH_PATTERN = re.compile(r"^[A-Za-z]{3}-\d{2}$")

REMOVE_STRINGS = [
    "Age Bucket: Less than 18",
    "Age Bucket: 18-21",
    "Age Bucket: 22-25",
    "Age Bucket: 26-28",
    "Age Bucket: 29-35",
    "Age Bucket: More than 35",
    "SUB TOTAL",
    "Grand Total",
    "STATEWISE NEW PAYROLL DATA (EPFO)",
    "Net New Payroll Statewise & Age Buckets",
]


# CSV CLEANING FUNCTIONS

def fill_missing_state(df):
    mask = (
        df.iloc[:, 0].astype(str).str.strip().str.lower()
        == "age bucket: less than 18"
    )
    for idx in df.index[mask]:
        if idx + 1 < len(df) and (
            pd.isna(df.iat[idx + 1, 0])
            or str(df.iat[idx + 1, 0]).strip() == ""
        ):
            df.iat[idx + 1, 0] = "State"
    return df


def extract_age_bucket(df):
    df["Age_Bucket"] = (
        df.iloc[:, 0]
        .apply(
            lambda x: (
                BUCKET_PATTERN.match(str(x)).group(1)
                if BUCKET_PATTERN.match(str(x))
                else None
            )
        )
        .ffill()
    )
    return df


def remove_unwanted_rows(df):
    df = df[
        ~df.iloc[:, 0].astype(str).str.strip().isin(REMOVE_STRINGS)
    ].reset_index(drop=True)
    return df


def promote_header(df):
    df.columns = df.iloc[0]
    df = df.drop(index=0).reset_index(drop=True)
    df.columns = df.columns.str.strip()
    df.rename(columns={"Less than 18": "Age_Bucket"}, inplace=True)
    return df


def remove_year_columns(df):
    df = df.loc[
        :,
        ~df.columns.astype(str)
        .str.strip()
        .str.match(YEAR_COL_PATTERN, na=False),
    ]
    return df


def remove_state_rows(df):
    df = df[
        ~df.apply(
            lambda row: row.astype(str).str.contains("State").any(), axis=1
        )
    ].reset_index(drop=True)
    return df


def clean_csv_file(file: Path, interim_dir: Path):
    df = pd.read_csv(file, header=None, dtype=str)

    df = fill_missing_state(df)
    df = extract_age_bucket(df)
    df = remove_unwanted_rows(df)
    df = promote_header(df)
    df = remove_year_columns(df)

    df = pd.concat([df.pop("Age_Bucket"), df], axis=1)
    df = remove_state_rows(df)

    interim_dir.mkdir(parents=True, exist_ok=True)

    output_file = interim_dir / file.name
    df.to_csv(output_file, index=False)

    print(f"Cleaned & saved: {output_file}")
    return output_file


def clean_all_files(input_dir: Path, interim_dir: Path):
    interim_dir.mkdir(parents=True, exist_ok=True)

    for file in input_dir.glob("*.csv"):
        clean_csv_file(file, interim_dir)

    print("Cleaning completed successfully.\n")


# BUILD MASTER FILE

def get_files_info(interim_dir: Path):
    files_info = []

    for file in interim_dir.glob("*.csv"):
        df = pd.read_csv(file, dtype=str)
        df.columns = df.columns.str.strip()

        month_cols = [c for c in df.columns if MONTH_PATTERN.match(c)]
        if not month_cols:
            continue

        month_dates = pd.to_datetime(
            [f"01-{m}" for m in month_cols], 
            format="%d-%b-%y",
            errors="coerce"
        )
        if month_dates.empty:
            continue

        latest_idx = month_dates.argmax()
        files_info.append(
            {
                "df": df,
                "latest_month_col": month_cols[latest_idx],
                "latest_month_dt": month_dates.max(),
            }
        )

    return sorted(files_info, key=lambda x: x["latest_month_dt"], reverse=True)


def collect_all_months(files_info):
    all_months = sorted(
        {
            col
            for f in files_info
            for col in f["df"].columns
            if MONTH_PATTERN.match(col)
        },
        key=lambda x: pd.to_datetime(f"01-{x}", format="%d-%b-%y"),
        reverse=True,
    )
    return all_months


def build_master_rows(files_info, all_months):
    master_rows = []

    for month in all_months:
        for f in files_info:
            if month in f["df"].columns:
                df_sel = f["df"][["Age_Bucket", "State", month]].copy()
                month_end = (
                    pd.to_datetime(f"01-{month}", format="%d-%b-%y")
                    + pd.offsets.MonthEnd(0)
                ).strftime("%d-%b-%Y")

                df_sel["Month"] = month_end
                df_sel = df_sel.rename(columns={month: "Net_Payroll"})

                df_sel = df_sel[
                    ["Month", "State", "Age_Bucket", "Net_Payroll"]
                ]

                master_rows.append(df_sel)
                break

    return master_rows


def build_master(interim_dir: Path):
    files_info = get_files_info(interim_dir)
    all_months = collect_all_months(files_info)
    master_rows = build_master_rows(files_info, all_months)

    master_df = pd.concat(master_rows, ignore_index=True)
    master_df.columns = [c.lower() for c in master_df.columns]

    master_df = master_df.apply(
        lambda x: x.str.title() if x.dtype == "object" else x
    )

    print(f"Master file built with {master_df.shape[0]:,} rows.\n")
    return master_df


# LOAD & MERGE STATE CODE MAPPING


def load_mapping(mapping_csv: Path):

    if not mapping_csv.exists():
        raise FileNotFoundError(f"Mapping CSV not found: {mapping_csv}")

    lines = mapping_csv.read_text(encoding="utf-8").splitlines()



    header_line_idx = None
    for i, line in enumerate(lines):
        if "State Code" in line and "State Name" in line:
            header_line_idx = i
            break

    if header_line_idx is None:
        raise ValueError("Could not find header row with 'State Code'.")



    df = pd.read_csv(mapping_csv, skiprows=header_line_idx)


    df = df[["State Code", "State Name (In English)"]].drop_duplicates()

    df["State Name (In English)"] = df["State Name (In English)"].str.strip().str.title()

    df.rename(
        columns={
            "State Code": "state_code",
            "State Name (In English)": "state",
        },
        inplace=True,
    )

    print(f"Loaded LGD mapping with {len(df)} states.")
    return df


def merge_with_state_codes(master_df, mapping_df, clean_dir: Path):
    clean_dir.mkdir(parents=True, exist_ok=True)

    master_df["state"] = master_df["state"].astype(str).str.strip().str.title()
    master_df["state"] = master_df["state"].replace(
        {"Chattisgarh": "Chhattisgarh", "Orissa": "Odisha"}
    )

    merged_df = master_df.merge(mapping_df, on="state", how="left")

    merged_df = merged_df[
        ["month", "state", "state_code", "age_bucket", "net_payroll"]
    ]


    manual_codes = {"Delhi": 7, "Chandigarh": 4}

    merged_df["state_code"] = merged_df.apply(
        lambda row: manual_codes.get(row["state"], row["state_code"]),
        axis=1,
    )

    merged_df["state_code"] = merged_df["state_code"].astype(str).str.zfill(2)

    merged_df["month"] = pd.to_datetime(
        merged_df["month"], format="%d-%b-%Y"
    ).dt.strftime("%d-%m-%Y")

    output_path = clean_dir / "Master_Survey_With_State_Code.csv"
    merged_df.to_csv(output_path, index=False)

    print(f"Final merged file saved: {output_path}")
    return merged_df


# MAIN EXECUTION

def main(input_dir: Path, interim_dir: Path, clean_dir: Path, mapping_csv: Path):
    clean_all_files(input_dir, interim_dir)
    master_df = build_master(interim_dir)
    mapping_df = load_mapping(mapping_csv)
    merge_with_state_codes(master_df, mapping_df, clean_dir)




if __name__ == "__main__":
    base = Path.cwd().parents[1] / "data"

    input_dir = base / "interim" / "parsed_pdfs"
    interim_dir = base / "interim"
    clean_dir = base / "processed"
    mapping_csv = base / "external" / "LGD_Latest 1.csv"

    main(input_dir, interim_dir, clean_dir, mapping_csv)
