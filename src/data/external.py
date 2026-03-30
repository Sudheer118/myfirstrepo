# script to extract the state_name, apmc_name, earlier_dates
import requests
import csv
import json
import time
import random
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
from requests.exceptions import RequestException

# CONFIG
STATES_URL = "https://enam.gov.in/web/ajax_ctrl/states_name"
APMC_URL = "https://enam.gov.in/web/Ajax_ctrl/apmc_list"
COMMODITY_URL = "https://enam.gov.in/web/Ajax_ctrl/commodity_list"

LANGUAGE = "en"
PORTAL_START = datetime(2016, 1, 1).date()            # base portal start (we special-case 2016-04-14)
TODAY = date.today()

DELAY_MIN = 1.0
DELAY_MAX = 2.5
TIMEOUT = 30
MAX_RETRIES = 3

#OUTPUT_DIR = Path(r"C:\Users\31965\Downloads\New folder")
OUTPUT_DIR = Path(__file__).resolve().parents[2]/"data/external"
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.csv"
RESULT_FILE_CSV = OUTPUT_DIR / "all_states_apmcs_earliest.csv"
RESULT_FILE_JSON = OUTPUT_DIR / "all_states_apmcs_earliest.json"

#  LOGGER 
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(OUTPUT_DIR / "scraper.log", encoding="utf-8"),
        logging.StreamHandler()  # This prints to terminal
    ]
)

#  SESSION 
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

#  HELPERS / CHECKPOINT
def random_delay():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        logging.info("Resuming from checkpoint...")
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    return []

def save_checkpoint(rows):
    # rows is a list of dicts with the final output columns
    with open(CHECKPOINT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["state_name", "state_id", "apmc_name", "apmc_id", "earliest_date"]
        )
        writer.writeheader()
        writer.writerows(rows)

#  FETCH FUNCTIONS 
def fetch_states(session):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.post(STATES_URL, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json().get("data", [])
        except RequestException as e:
            logging.error(f"fetch_states attempt {attempt} failed: {e}")
            time.sleep(min(5, 2 ** attempt))
    raise Exception("Failed to fetch states after retries")

def fetch_apmcs(session, state_id):
    payload = {"state_id": state_id}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.post(APMC_URL, data=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json().get("data", [])
        except RequestException as e:
            logging.error(f"[state_id={state_id}] fetch_apmcs attempt {attempt} failed: {e}")
            time.sleep(min(5, 2 ** attempt))
    logging.warning(f"[state_id={state_id}] Could not fetch APMCs after retries")
    return []

def fetch_range(session, state_name, apmc_name, start, end):
    payload = {
        "language": LANGUAGE,
        "stateName": state_name,
        "apmcName": apmc_name,
        "fromDate": start.strftime("%Y-%m-%d"),
        "toDate": end.strftime("%Y-%m-%d"),
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.post(COMMODITY_URL, data=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except RequestException as e:
            logging.error(f"[{apmc_name}] fetch_range attempt {attempt} ({start} -> {end}) failed: {e}")
            time.sleep(min(5, 2 ** attempt))
    logging.warning(f"[{apmc_name}] Failed to fetch range {start} -> {end} after {MAX_RETRIES} attempts")
    return None

def contains_data(response):
    return bool(response and "data" in response and len(response["data"]) > 0)

def extract_earliest_from_response(response):
    # If the response contains created_at fields, pick earliest directly to avoid further refine
    try:
        dates = []
        for r in response.get("data", []):
            # try multiple possible date keys just in case (common key used earlier: created_at)
            if "created_at" in r:
                dates.append(datetime.strptime(r["created_at"], "%Y-%m-%d").date())
            elif "created" in r:
                dates.append(datetime.strptime(r["created"], "%Y-%m-%d").date())
        return min(dates) if dates else None
    except Exception:
        return None

# SEARCH (year-first then binary refine) 
def refine_range_iter(session, state_name, apmc_name, start, end):
    # iterative binary search to avoid recursion depth for large ranges
    s = start
    e = end
    while (e - s).days > 1:
        mid = s + timedelta(days=((e - s).days // 2))
        resp = fetch_range(session, state_name, apmc_name, s, mid)
        if contains_data(resp):
            e = mid
        else:
            s = mid + timedelta(days=1)
        random_delay()
    return s

def find_earliest_date(session, state_name, apmc_name):
    # Year-wise scan first, then refine inside the year where data appears
    start = PORTAL_START
    end = TODAY
    for year in range(start.year, end.year + 1):
        # start of this year (special-case 2016)
        if year == 2016:
            y_start = date(2016, 4, 14)
        else:
            y_start = date(year, 1, 1)
        # end of this year: if current year use TODAY else 31-Dec
        y_end = TODAY if year == TODAY.year else date(year, 12, 31)

        resp = fetch_range(session, state_name, apmc_name, y_start, y_end)
        random_delay()
        if contains_data(resp):
            # try extract earliest directly from that response (saves refine calls)
            earliest = extract_earliest_from_response(resp)
            if earliest:
                return earliest
            # otherwise refine inside this year's range
            return refine_range_iter(session, state_name, apmc_name, y_start, y_end)
    return None

#  MAIN 
def main():
    results = load_checkpoint()         # list of dicts already processed
    completed = {(r["state_id"], r["apmc_id"]) for r in results} if results else set()

    with requests.Session() as sess:
        sess.headers.update({"User-Agent": "Mozilla/5.0"})
        states = fetch_states(sess)
        logging.info(f"Fetched {len(states)} states")

        for s_idx, s in enumerate(states, start=1):
            state_name = s.get("state_name")
            state_id = s.get("state_id")
            logging.info(f"[{s_idx}/{len(states)}] Processing state: {state_name} ({state_id})")

            apmcs = fetch_apmcs(sess, state_id)
            logging.info(f"[{state_name}] Found {len(apmcs)} APMCs")

            for a_idx, a in enumerate(apmcs, start=1):
                apmc_name = a.get("apmc_name")
                apmc_id = a.get("apmc_id")

                key = (str(state_id), str(apmc_id))
                if (state_id, apmc_id) in completed or (str(state_id), str(apmc_id)) in completed:
                    logging.info(f"Skipping already completed {apmc_name} ({apmc_id})")
                    continue

                logging.info(f"[{state_name}][{a_idx}/{len(apmcs)}] Finding earliest for: {apmc_name} ({apmc_id})")
                earliest = find_earliest_date(sess, state_name, apmc_name)

                record = {
                    "state_name": state_name,
                    "state_id": state_id,
                    "apmc_name": apmc_name,
                    "apmc_id": apmc_id,
                    "earliest_date": earliest.strftime("%Y-%m-%d") if earliest else "NONE"
                }
                results.append(record)
                # persist after every APMC so we can resume
                save_checkpoint(results)
                logging.info(f"Saved checkpoint: {state_name} / {apmc_name} -> {record['earliest_date']}")

                random_delay()

    # final save (CSV + JSON)
    if results:
        with open(RESULT_FILE_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["state_name", "state_id", "apmc_name", "apmc_id", "earliest_date"])
            writer.writeheader()
            writer.writerows(results)

        with open(RESULT_FILE_JSON, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2, ensure_ascii=False)

        logging.info(f"Done. Results saved to: {RESULT_FILE_CSV} and {RESULT_FILE_JSON}")
        print(f"Done. Results saved to: {RESULT_FILE_CSV}")
    else:
        logging.info("No results to save.")

if __name__ == "__main__":
    main()
