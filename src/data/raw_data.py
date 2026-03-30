from pathlib import Path
import csv
import time
import random
import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

#  CONFIG

BASE_URL = "https://kaushalbharat.gov.in/candidateview"

MAX_STATE_WORKERS = 3
MAX_RETRIES = 5
BACKOFF_BASE = 1.5


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data/raw"
PART_DIR = OUTPUT_DIR / "parts1"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PART_DIR.mkdir(exist_ok=True)
CHECKPOINT_DIR.mkdir(exist_ok=True)

#  SESSION

def create_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    return s

def fetch_with_retry(session, url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 200 and r.text.strip():
                return r.text
        except:
            pass
        time.sleep(BACKOFF_BASE ** attempt + random.uniform(0.5, 1.5))
    raise RuntimeError("Blocked / Network issue")

def get_soup(session, url):
    soup = BeautifulSoup(fetch_with_retry(session, url), "lxml")
    if not soup.find("table"):
        raise RuntimeError("Blocked HTML")
    return soup

# CHECKPOINT

def cp_files(state):
    return (
        CHECKPOINT_DIR / f"{state}_discovered.json",
        CHECKPOINT_DIR / f"{state}_completed.json",
    )

def load_set(path):
    if path.exists():
        return set(json.loads(path.read_text(encoding="utf-8")))
    return set()

def save_set(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(sorted(data)), encoding="utf-8")
    tmp.replace(path)

def clear_state_cp(state):
    for f in cp_files(state):
        if f.exists():
            f.unlink()

# UTIL 

def state_done(state):
    return (OUTPUT_DIR / f"{state}_candidate_wise.csv").exists()

def find_column_index(row, key):
    for i, th in enumerate(row.find_all("th")):
        if key.lower() in th.get_text(strip=True).lower():
            return i
    return None

# CANDIDATE 

def extract_candidate_table(session, url, tcid, batch_vals):
    soup = get_soup(session, url)
    table = soup.find("table")

    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    headers = ["TC ID", "Batch Start Date", "Batch End Date", "Monthly Continuity"] + headers

    tbody = table.find("tbody")
    if not tbody:
        return None, None

    tds = tbody.find_all("td")
    cols = len(headers) - 4

    rows = []
    for i in range(0, len(tds), cols):
        rows.append(
            [tcid] + batch_vals +
            [tds[j].get_text(strip=True) for j in range(i, i + cols)]
        )

    return headers, rows

# STATE WORKER

def process_state(state, url):

    print(f"\nSTATE: {state}")

    final = OUTPUT_DIR / f"{state}_candidate_wise.csv"
    part = PART_DIR / f"{state}_candidate_wise.part.csv"

    discovered_f, completed_f = cp_files(state)
    discovered = load_set(discovered_f)
    completed = load_set(completed_f)

    session = create_session()

    try:
        soup = get_soup(session, url)
        table = soup.find("table")
        sanction_idx = find_column_index(table.find_all("tr")[0], "Sanction")

        with part.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            write_header = f.tell() == 0

            for srow in table.find_all("tr")[1:]:
                scols = srow.find_all("td")
                if len(scols) <= sanction_idx:
                    continue

                sanc = scols[sanction_idx].find("a", href=True)
                if not sanc:
                    continue

                st = get_soup(session, sanc["href"]).find("table")
                hdr = st.find_all("tr")[0]
                tc_idx = find_column_index(hdr, "TC")
                tcid_idx = find_column_index(hdr, "TC ID")

                for tcrow in st.find_all("tr")[1:]:
                    tcols = tcrow.find_all("td")
                    if len(tcols) <= max(tc_idx, tcid_idx):
                        continue

                    tcid = tcols[tcid_idx].get_text(strip=True)
                    tca = tcols[tc_idx].find("a", href=True)
                    if not tca:
                        continue

                    tt = get_soup(session, tca["href"]).find("table")
                    bheader = tt.find_all("tr")[0]

                    bidx = find_column_index(bheader, "Batch")
                    bs = find_column_index(bheader, "Batch Start")
                    be = find_column_index(bheader, "Batch End")
                    mc = find_column_index(bheader, "Monthly Continuity")

                    for brow in tt.find_all("tr")[1:]:
                        bcols = brow.find_all("td")
                        if len(bcols) <= bidx:
                            continue

                        batch_vals = [
                            bcols[bs].get_text(strip=True) if bs is not None else "",
                            bcols[be].get_text(strip=True) if be is not None else "",
                            bcols[mc].get_text(strip=True) if mc is not None else "",
                        ]

                        for ba in bcols[bidx].find_all("a", href=True):
                            bid = ba["href"].split("batch_id=")[-1]

                            discovered.add(bid)
                            save_set(discovered_f, discovered)

                            if bid in completed:
                                continue

                            headers, rows = extract_candidate_table(
                                session, ba["href"], tcid, batch_vals
                            )

                            if headers is None:
                                continue

                            if rows:
                                if write_header:
                                    writer.writerow(headers)
                                    write_header = False

                                writer.writerows(rows)
                                f.flush()

                            completed.add(bid)
                            save_set(completed_f, completed)

                            time.sleep(random.uniform(0.8, 1.5))

        #  FINALIZE ONLY IF FULLY COMPLETE
        if discovered and discovered == completed:
            part.replace(final)
            clear_state_cp(state)
            print(f"{state} DONE (all batches)")
        else:
            print(f"{state} PARTIAL — will resume")

    except Exception as e:
        print(f"{state} FAILED will resume later:", e)

#  MAIN 

def main():
    session = create_session()
    soup = get_soup(session, BASE_URL)
    rows = soup.find("table").find_all("tr")
    state_idx = find_column_index(rows[0], "State")

    with ThreadPoolExecutor(max_workers=MAX_STATE_WORKERS) as ex:
        futures = []

        for r in rows[1:]:
            cols = r.find_all("td")
            if len(cols) <= state_idx:
                continue

            a = cols[state_idx].find("a", href=True)
            if not a:
                continue

            state = a.get_text(strip=True)
            if state_done(state):
                print("SKIP COMPLETED:", state)
                continue

            futures.append(ex.submit(process_state, state, a["href"]))

        for _ in as_completed(futures):
            pass

    print("\nALL FINISHED")

if __name__ == "__main__":
    main()
