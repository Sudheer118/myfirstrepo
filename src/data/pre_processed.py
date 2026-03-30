# This script preprocess the data
import pandas as pd
import numpy as np
import re
from pathlib import Path

# PATHS
BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_DIR = BASE_DIR / "data/interim"

OUTPUT_DIR = BASE_DIR / "data/processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUTPUT_DIR / "processed_all_years.csv"



# NORMALIZE
def norm(x):
    return (
        str(x).lower()
        .replace("&", "and")
        .replace("-", " ")
        .replace(".", "")
        .strip()
    )

# EXTRACT YEAR FOR SORTING
def extract_start_year(file_path):
    m = re.search(r"(\d{4})-(\d{2})", file_path.stem)
    return int(m.group(1)) if m else 9999



# PROCESS SINGLE FILE

def process_file(INPUT_CSV):

    df = pd.read_csv(INPUT_CSV, header=2, dtype=str, low_memory=False)


    df.columns = df.columns.str.replace("\n", " ").str.strip()
    df = df.iloc[:, :-1]
    df = df.replace(r"\s*\n\s*", " ", regex=True)


    year_match = re.search(r"\d{4}-\d{2}", INPUT_CSV.stem)
    df["year"] = year_match.group(0) if year_match else None

    #REMOVE JUNK
    df = df[
        ~df.iloc[:, 1].str.contains("Labour Category", case=False, na=False) &
        ~df.iloc[:, 0].str.startswith("Average", na=False) &
        ~df.iloc[:, 0].str.contains("Table", case=False, na=False)
    ].reset_index(drop=True)

    # STRUCTURE
    df.insert(0, "state", np.nan)
    df.insert(1, "district", np.nan)
    df = df.rename(columns={"State/District/Center": "center"})

    # EXTRACT GEO 
    df["state"] = np.where(
        df["center"].str.contains(r"^state\s*:", case=False, na=False),
        df["center"].str.split(":", n=1).str[-1].str.strip(),
        np.nan
    )

    df["district"] = np.where(
        df["center"].str.contains(r"^district\s*:", case=False, na=False),
        df["center"].str.split(":", n=1).str[-1].str.strip(),
        np.nan
    )

    df["center"] = np.where(
        df["center"].str.contains(r"^center\s*:", case=False, na=False),
        df["center"].str.split(":", n=1).str[-1].str.strip(),
        df["center"]
    )

    df[["state", "district", "center"]] = df[["state", "district", "center"]].ffill()

    df = df[
        ~df["center"].str.contains(
            r"^state\s*:|^district\s*:|^center\s*:",
            case=False,
            na=False
        )
    ].reset_index(drop=True)

    df["center"] = (
        df["center"]
        .str.replace(r"\bFIELD LABOUR\b", "", regex=True, case=False)
        .str.replace(r"\bSKILLED\b", "", regex=True, case=False)
        .str.replace(r"\bOTHER\b", "", regex=True, case=False)
        .str.strip()
    )

    df[["Labour Category", "Labour Type"]] = (
        df[["Labour Category", "Labour Type"]].ffill()
    )

    #  MONTH → LONG 
    month_cols = df.columns[df.columns.str.match(r"^[A-Z][a-z]{2}$")]

    id_cols = [
        "state", "district", "center",
        "Labour Category", "Labour Type",
        "Gen", "Annual Average", "year"
    ]

    long_df = df.melt(
        id_vars=id_cols,
        value_vars=month_cols,
        var_name="month_name",
        value_name="monthly_average_wage"
    )

    month_num = pd.to_datetime(long_df["month_name"], format="%b").dt.month
    start_year = long_df["year"].str[:4].astype(int)
    end_year = (start_year // 100) * 100 + long_df["year"].str[-2:].astype(int)
    calendar_year = np.where(month_num >= 7, start_year, end_year)

    long_df["month"] = pd.to_datetime(
        dict(year=calendar_year, month=month_num, day=1)
    ).dt.strftime("%d-%m-%Y")

    final_df = long_df.drop(columns=["month_name", "year"])
    
    final_df.insert(0, "month", final_df.pop("month"))


    return final_df



# MAIN LOOP

all_files = sorted(
    INPUT_DIR.glob("*.csv"),
    key=extract_start_year
)

final_list = []

for file in all_files:
    print("Processing:", file.name)
    final_list.append(process_file(file))

final_df = pd.concat(final_list, ignore_index=True)

final_df.columns = final_df.columns.str.lower().str.replace(" ", "_")

for col in final_df.columns:
    if final_df[col].dtype == "object":
        final_df[col] = final_df[col].str.title()

# SAVE

final_df.to_csv(OUTPUT_CSV, index=False)

print(" All years concatenated and saved:", OUTPUT_CSV)
