#script to extract the trade data
import requests
import csv
import json
import time
import random
from datetime import datetime, timedelta, date
from pathlib import Path
from requests.exceptions import RequestException


#  CONFIG 

TRADE_URL = "https://enam.gov.in/web/Ajax_ctrl/trade_data_list"
TODAY = date.today()

OUTPUT_DIR = Path(__file__).resolve().parents[2]/"data/raw"
EARLIEST_DATES_FILE = Path(__file__).resolve().parents[2]/"data/external/all_states_apmcs_earliest.csv"
OUTPUT_CSV = OUTPUT_DIR /"full_trade_data.csv"
OUTPUT_JSON = OUTPUT_DIR /"full_trade_data3.json"
CHECKPOINT_FILE = OUTPUT_DIR/"apmc_checkpoint.json"

#  CHECKPOINT 

def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {}


def save_checkpoint(state_name, apmc_name, last_date):
    ck = load_checkpoint()
    ck[f"{state_name}|{apmc_name}"] = last_date
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(ck, f, indent=2)


#  FIXED FUNCTION — CHUNKED API CALL 

def fetch_trade_data_in_chunks(session, state_name, apmc_name, start_date, end_date):
    """Fetch trade data MONTH-WISE to avoid 500 Server Error"""

    all_data = []
    current = start_date

    while current <= end_date:

        # Start of chunk
        chunk_start = current

        # End of month
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        chunk_end = next_month - timedelta(days=1)

        if chunk_end > end_date:
            chunk_end = end_date

        print(f"   ↳ Fetching chunk {chunk_start} → {chunk_end}")

        payload = {
            "commodityName": "-- Select Commodity --",
            "stateName": state_name,
            "apmcName": apmc_name,
            "fromDate": chunk_start.strftime("%Y-%m-%d"),
            "toDate": chunk_end.strftime("%Y-%m-%d")
        }

        # Delay
        time.sleep(random.uniform(1.0, 2.3))

        # First attempt
        try:
            resp = session.post(TRADE_URL, data=payload, timeout=40)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            all_data.extend(data)

        except Exception as e:
            print(f"   Chunk failed ({e}). Retrying in 3 sec...")
            time.sleep(3)

            # Second attempt
            resp = session.post(TRADE_URL, data=payload, timeout=40)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            all_data.extend(data)

        # Move to next chunk
        current = chunk_end + timedelta(days=1)

    return all_data


#  SAVE FUNCTION 

def save_data(state_name, apmc_name, data, all_json, seen):

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as out_csv:
        writer = csv.DictWriter(out_csv, fieldnames=[
            "state_name", "apmc_name", "commodity",
            "min_price", "modal_price", "max_price",
            "arrivals", "traded_qty", "unit", "date"
        ])

        for d in data:

            row_id = (
                state_name,
                apmc_name,
                d.get("commodity"),
                d.get("created_at")
            )

            if row_id in seen:
                continue

            row = {
                "state_name": state_name,
                "apmc_name": apmc_name,
                "commodity": d.get("commodity"),
                "min_price": d.get("min_price"),
                "modal_price": d.get("modal_price"),
                "max_price": d.get("max_price"),
                "arrivals": d.get("commodity_arrivals"),
                "traded_qty": d.get("commodity_traded"),
                "unit": d.get("Commodity_Uom"),
                "date": d.get("created_at")
            }

            writer.writerow(row)
            all_json.append(row)
            seen.add(row_id)


#  MAIN FUNCTION 

def main():

    # Load earliest dates
    with open(EARLIEST_DATES_FILE, "r", encoding="utf-8") as f:
        earliest_rows = list(csv.DictReader(f))

    # Create CSV header if needed
    if not OUTPUT_CSV.exists():
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as out_csv:
            writer = csv.DictWriter(out_csv, fieldnames=[
                "state_name", "apmc_name", "commodity",
                "min_price", "modal_price", "max_price",
                "arrivals", "traded_qty", "unit", "date"
            ])
            writer.writeheader()

    # Load JSON (avoid duplicates)
    all_json = []
    seen = set()

    if OUTPUT_JSON.exists():
        with open(OUTPUT_JSON, "r", encoding="utf-8") as jf:
            all_json = json.load(jf)
            for d in all_json:
                seen.add((d["state_name"], d["apmc_name"], d["commodity"], d["date"]))

    checkpoint = load_checkpoint()
    session = requests.Session()

    # Loop APMCs
    for row in earliest_rows:

        state_name = row["state_name"]
        apmc_name = row["apmc_name"]
        if row["earliest_date"] == "NONE":
            continue
        earliest_date = datetime.strptime(row["earliest_date"], "%Y-%m-%d").date()

        key = f"{state_name}|{apmc_name}"

        # Resume from last checkpoint
        if key in checkpoint:
            last_done = datetime.strptime(checkpoint[key], "%Y-%m-%d").date()
            if last_done >= TODAY:
                print(f"Skipping (already done): {state_name} / {apmc_name}")

                continue
            start_date = last_done + timedelta(days=1)
        else:
            start_date = earliest_date

        print(f"\n→ Fetching {state_name} / {apmc_name}")
        print(f"  From: {start_date}  To: {TODAY}")

        # MONTH-WISE DATA (SAFE)
        data = fetch_trade_data_in_chunks(session, state_name, apmc_name, start_date, TODAY)

        # Save data
        save_data(state_name, apmc_name, data, all_json, seen)

        # Update checkpoint
        save_checkpoint(state_name, apmc_name, TODAY.strftime("%Y-%m-%d"))

        # Save JSON
        with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
            json.dump(all_json, jf, indent=2)

        # Cooldown
        time.sleep(random.uniform(2, 5))

    print("\n DONE — Full trade data saved successfully!")


# Run script
if __name__ == "__main__":
    main()
