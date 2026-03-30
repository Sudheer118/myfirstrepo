# This script extracts the data
from pathlib import Path
import pdfplumber
import pandas as pd

#  CONFIG 
BASE_DIR = Path(__file__).resolve().parents[2]
PDF_DIR = BASE_DIR / "data/raw"
OUT_DIR = BASE_DIR / "data/interim"
OUT_DIR.mkdir(exist_ok=True)

SKIP_PAGES = 34

START_PATTERNS = [
    "Average Daily Agricultural Wages and Non Agricultural Wages (in Rs.)",
    "Average Daily Agricultural Wages (in Rs.)",
]

STOP_PATTERNS = [
    "PROFORMA FOR AGRICULTURAL WAGES",
    "Number of Districts & Center",
    "***"
]


def has_start(text):
    text = text.lower()
    return any(p.lower() in text for p in START_PATTERNS)

def has_stop(text):
    text = text.lower()
    return any(p.lower() in text for p in STOP_PATTERNS)

for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
    print(f"\n Processing: {pdf_path.name}")

    all_dfs = []

    with pdfplumber.open(pdf_path) as pdf:
        start_found = False

        for page_idx in range(SKIP_PAGES, len(pdf.pages)):
            page = pdf.pages[page_idx]
            text = page.extract_text() or ""

            # START
            if not start_found and has_start(text):
                start_found = True
                print(f"   Start found at page {page_idx + 1}")

            # STOP (any condition)
            if start_found and has_stop(text):
                print(f"   Stop found at page {page_idx + 1}")
                break

            # Extract tables
            if start_found:
                tables = page.extract_tables()

                for tbl in tables:
                    df = pd.DataFrame(tbl)
                    df["page_no"] = page_idx + 1
                    all_dfs.append(df)

    # SAVE PER PDF
    if all_dfs:
        out_csv = OUT_DIR / f"{pdf_path.stem}.csv"
        pd.concat(all_dfs, ignore_index=True).to_csv(out_csv, index=False)
        print(f"   Saved: {out_csv.name}")
    else:
        print("   No tables extracted for this PDF")
