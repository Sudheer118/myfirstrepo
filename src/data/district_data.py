import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path

URL = "https://kaushalbharat.gov.in/out-candidate-registration/trades-centrelist"

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data/raw/district_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "training_centres_all_states_clean.csv"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Referer": URL,
    "Origin": "https://kaushalbharat.gov.in",
    "Content-Type": "application/x-www-form-urlencoded"
})


# GET PAGE → CSRF TOKEN

resp = session.get(URL)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "lxml")
csrf = soup.find("input", {"name": "_csrf"})["value"]


# POST → FETCH DATA

payload = {
    "_csrf": csrf,
    "submit": "Submit_but"
}

resp = session.post(URL, data=payload)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "lxml")
table = soup.find("table", id="tctrade")
tbody = table.find("tbody")


# HEADERS (TC ID after TC Name)

headers = [th.get_text(strip=True) for th in table.find_all("th")]

tc_name_index = headers.index("Training Centre Name")
headers.insert(tc_name_index + 1, "TC ID")

rows = []


# ROW PROCESSING

for tr in tbody.find_all("tr"):
    tds = tr.find_all("td")
    if not tds:
        continue

    row = [td.get_text(" ", strip=True) for td in tds]

    tc_name = row[tc_name_index]
    tc_id = ""

    # Extract TC ID and clean name
    if "(" in tc_name and ")" in tc_name:
        tc_id = tc_name.split("(")[-1].replace(")", "").strip()
        tc_name = tc_name.split("(")[0].strip()

    # Update row
    row[tc_name_index] = tc_name
    row.insert(tc_name_index + 1, tc_id)

    rows.append(row)

print("Total rows scraped:", len(rows))


# SAVE CSV

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"File saved at: {OUTPUT_FILE}")
