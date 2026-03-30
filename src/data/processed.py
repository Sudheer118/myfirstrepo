#  Script to process and map trade data

import json
import csv
from pathlib import Path
import pandas as pd

# FILE PATHS

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "data/processed"
RAW_JSON = BASE_DIR / "data/raw/full_trade_data3.json"
LGD_FILE = BASE_DIR / "data/external/all_states_apmcs_earliest.csv"

CSV_FILE = OUTPUT_DIR / "full_trade_data1.csv"
PARQUET_FILE = OUTPUT_DIR / "full_trade_data.parquet"


# JSON → CSV

def json_to_csv(json_path: Path, csv_path: Path) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    print("JSON converted to CSV successfully")



# PROCESS + MERGE LGD

def process_trade_data(csv_path: Path, parquet_path: Path) -> None:
    
    # LOAD MAIN CSV
    
    df = pd.read_csv(csv_path)
    print("Total rows:", len(df))


    # TITLE CASE
    
    for col in ["state_name", "apmc_name", "commodity"]:
        df[col] = df[col].where(
            df[col].isnull(),
            df[col].astype(str).str.title()
        )


    # SORTING 
    
    df.sort_values(
        by=["state_name", "apmc_name", "commodity", "date"],
        kind="stable",
        inplace=True
    )
    df.reset_index(drop=True, inplace=True)


    # LOAD LGD FILE
    
    df_lgd = pd.read_csv(LGD_FILE)

    df_lgd = df_lgd[
        ["state_name", "apmc_name", "state_id", "apmc_id"]
    ].rename(
        columns={
            "state_id": "state_code",
            "apmc_id": "apmc_code"
        }
    )

    df_lgd["state_name"] = df_lgd["state_name"].str.title()
    df_lgd["apmc_name"] = df_lgd["apmc_name"].str.title()


    # MERGE LGD CODES
    
    df = df.merge(
        df_lgd,
        on=["state_name", "apmc_name"],
        how="left"
    )


    # ZERO-PAD CODES
    
    df["state_code"] = (
        df["state_code"]
        .astype("Int64")
        .astype(str)
        .str.zfill(3)
    )

    df["apmc_code"] = (
        df["apmc_code"]
        .astype("Int64")
        .astype(str)
        .str.zfill(4)
    )

    desired_order = [
    "date",
    "state_name",
    "state_code",
    "apmc_name",
    "apmc_code",
    "commodity",
    "arrivals",
    "traded_qty",
    "min_price",
    "modal_price",
    "max_price",
    "unit",
]

    df = df[desired_order]
    # SAVE FINAL OUTPUTS
    
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)

    print("Final data saved as CSV and Parquet")



# RUN

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_to_csv(RAW_JSON, CSV_FILE)
    process_trade_data(CSV_FILE, PARQUET_FILE)
