import logging
import re
import time
from pathlib import Path

import pandas as pd
import pdfplumber

logging.getLogger("pdfminer").setLevel(logging.ERROR)


APPENDIX_PATTERNS = [
    ["Appendix A", "Detailed Tables"],
    [
        "Appendix A",
        "List of Detailed Tables",
        "(hyperlinked with the corresponding Excel table)",
    ],
]

PATTERNS = [
    "Percentage distribution of persons of age 15 years and above in usual status (ps+ss) for each million plus cities",
    "Percentage distribution of persons in labour force in Current Weekly Status (CWS) by number of days unemployed",
]

pattern_shape_list = [
    (
        re.compile(
            r"(?i)(general\s+educational\s+level\*?\s+for\s+each\s+state/?ut|percentage\s+distribution\s+of\s+persons\s+of\s+age\s+15\s+years\s+and\s+above\s+by\s+highest\s+level\s+of\s+education\s+successfully\s+completed\s+for\s+each\s+state/?ut)"
        ),
        10,
        10,
        "general_educational_level",
    ),
    (
        re.compile(
            r"(?i)\(ps\+ss\)\s+by\s+broad\s+status\s+in\s+employment\s+for\s+each\s+state/?ut"
        ),
        10,
        6,
        "broad_status_employment",
    ),
    (
        re.compile(
            r"(?i)\(LFPR\)\s+\(in\s+per\s+cent\)\s+according\s+to\s+usual\s+status\s+\(ps\+ss\)\s+for\s+persons?\s+of\s+age\s+15\s+years\s+and\s+above"
        ),
        10,
        10,
        "labour_force_participation_rate",
    ),
    (
        re.compile(
            r"(?i)\(WPR\)\s+\(in\s+per\s+cent\)\s+according\s+to\s+usual\s+status\s+\(ps\+ss\)\s+for\s+persons?\s+of\s+age\s+15\s+years\s+and\s+above"
        ),
        10,
        10,
        "worker_population_ratio",
    ),
    (
        re.compile(
            r"(?i)\(UR\)\s+\(in\s+per\s+cent\)\s+according\s+to\s+usual\s+status\s+\(ps\+ss\)\s+for\s+persons?\s+of\s+age\s+15\s+years\s+and\s+above"
        ),
        10,
        10,
        "unemployment_rate",
    ),
    (
        re.compile(
            r":\s*Percentage\s+distribution\s+of\s+usually\s+working\s+persons\s+\(ps\+ss\)\s+by\s+industry\s+of\s+work(?:\s+for\s+each\s+State/\s*UT|\s+\(industry\s+sections\s+of\s+NIC-2008\))",
            re.IGNORECASE,
        ),
        10,
        10,
        "industry_of_work",
    ),
    (
        re.compile(
            r"(?i)labour\s+force\s+participation\s+rate\s+\(lfpr\)\s+\(in\s+per\s+cent\)\s+according\s+to\s+usual\s+status\s+\(ps\+ss\)\s+for\s+each\s+decile\s+class"
        ),
        10,
        10,
        "lfpr_decile",
    ),
    (
        re.compile(
            r"(?i)worker\s+population\s+ratio\s+\(wpr\)\s+\(in\s+per\s+cent\)\s+according\s+to\s+usual\s+status\s+\(ps\+ss\)\s+for\s+each\s+decile\s+class"
        ),
        10,
        10,
        "wpr_decile",
    ),
    (
        re.compile(
            r"(?i)unemployment\s+rate\s+\(ur\)\s+\(in\s+per\s+cent\)\s+according\s+to\s+usual\s+status\s+\(ps\+ss\)\s+for\s+each\s+decile\s+class"
        ),
        10,
        10,
        "ur_decile",
    ),
    (
        re.compile(
            r"(?i)\(CWS\)\s+by\s+broad\s+status|CWS\s+by\s+broad\s+status"
        ),
        10,
        6,
        "cws_broad_status",
    ),
    (
        re.compile(
            r"(?i)(industry:\s*\(\s*\d{2,3}(?:\s*,\s*\d{2,3})*\s*,?\s*\d{2}-\d{2}\s*\)|\(industry\s+divisions\s+\d{2}-\d{2}\s+of\s+nic-?\d{4}\)\s+by\s+enterprise\s+type)"
        ),
        10,
        10,
        "industry_enterprise_type",
    ),
    (
        re.compile(
            r"(?i)average\s+wage/?salary\s+earnings\s*\(rs\.\s*0\.00\)\s+during\s+the\s+preceding\s+calendar\s+month\s+from\s+regular\s+wage/?salaried\s+employment\s+among"
        ),
        10,
        10,
        "average_regular_wage",
    ),
    (
        re.compile(
            r"Average wage earnings \(Rs\. \d+\.\d{2}\) per day from casual labour work other than public works in CWS"
        ),
        10,
        10,
        "average_casual_wage",
    ),
    (
        re.compile(r"(?i)self-?employed\s+persons\s+in\s+CWS"),
        10,
        10,
        "self_employed",
    ),
    (
        re.compile(
            r"labour\s+force\s+participation\s+rate.*?\(lfpr\).*?\(in\s+per\s*cent\).*?according\s+to\s+current\s+weekly\s+status\s+for\s+each\s+state\s*/?\s*ut.*?age\s+group[s]?:?\s*15\s+years\s+and\s+above",
            re.IGNORECASE | re.DOTALL,
        ),
        10,
        10,
        "lfpr_cws",
    ),
    (
        re.compile(
            r"worker\s+population\s+ratio.*?\(wpr\).*?\(in\s+per\s*cent\).*?according\s+to\s+current\s+weekly\s+status\s+for\s+each\s+state\s*/?\s*ut.*?age\s+group[s]?:?\s*15\s+years\s+and\s+above",
            re.IGNORECASE | re.DOTALL,
        ),
        10,
        10,
        "wpr_cws",
    ),
    (
        re.compile(
            r"labour\s+force\s+participation\s+rate\s+\(lfpr\)\s+\(in\s+per\s+cent\)\s+according\s+to\s+usual\s+status\s+\(ps\+ss\)\s+for\s+each\s+state/?ut",
            re.IGNORECASE,
        ),
        10,
        10,
        "lfpr_usual_state",
    ),
    (
        re.compile(
            r"(?i)\(WPR\)\s+\(in\s+per\s+cent\)\s+according\s+to\s+usual\s+status\s+\(ps\+ss\)\s+for\s+each\s+state/?ut"
        ),
        10,
        10,
        "wpr_usual_state",
    ),
    (
        re.compile(
            r"Unemployment Rate \(UR\) \(in per cent\) according to usual status \(ps\+ss\) for each State/UT"
        ),
        10,
        10,
        "ur_usual_state",
    ),
    (re.compile(r"(?i)<hours"), 10, 10, "hours_worked"),
]


def contains_pattern(text, patterns):
    text_lower = text.lower()
    return any(pat.lower() in text_lower for pat in patterns)


def parse_table_title(cell_value: str):
    if not isinstance(cell_value, str):
        return None, None
    match = re.search(r"Table\s*\((\d+)\)", cell_value, re.IGNORECASE)
    if not match:
        return None, None
    table_num = match.group(1)
    folder_name = f"table_{table_num}"
    lower_val = cell_value.lower()
    normalized_val = re.sub(r"\s*\+\s*", "+", lower_val)

    if "rural+urban" in normalized_val:
        file_name = "total.csv"
    elif "rural" in normalized_val:
        file_name = "rural.csv"
    elif "urban" in normalized_val:
        file_name = "urban.csv"
    else:
        file_name = "other.csv"

    return folder_name, file_name


def extract_month_from_title(title_row: str):
    if not isinstance(title_row, str):
        return None
    match = re.search(
        r"([A-Za-z]{3,9}\s*-\s*[A-Za-z]{3,9})\s*(20\d{2}|2[0-4])", title_row
    )
    if match:
        month_str = "-".join(
            [m[:3].title() for m in match.group(1).split("-")]
        )
        year_str = match.group(2)
        return f"{month_str}-{year_str}"
    return None


def extract_year_from_filename(filename: str) -> str:
    match1 = re.search(r"(\d{4}-\d{2})", filename)
    if match1:
        return match1.group(1)
    match2 = re.search(r"(\d{4})[_-](\d{2})", filename)
    if match2:
        return f"{match2.group(1)}-{match2.group(2)}"
    match3 = re.search(r"(\d{2})[_-](\d{2})", filename)
    if match3:
        start = int(match3.group(1))
        end = match3.group(2)
        start_full = 2000 + start
        return f"{start_full}-{end}"
    return "unknown_year"


def find_appendix_page(pdf):
    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines in APPENDIX_PATTERNS:
            return i
    return None


def find_page_range(pdf, appendix_page, skip_pages, stop_patterns):
    start_scan_page = appendix_page + skip_pages
    total_pages = len(pdf.pages)
    if start_scan_page > total_pages:
        return None
    for i, page in enumerate(
        pdf.pages[start_scan_page - 1 :], start=start_scan_page
    ):
        text = page.extract_text() or ""
        if contains_pattern(text, stop_patterns):
            return list(range(appendix_page, i + 1))
    return None


def extract_tables(pdf, page_range, pattern, min_rows, min_cols):
    tables_all = []
    for page_num in page_range:
        page = pdf.pages[page_num - 1]
        text = page.extract_text() or ""
        if not pattern.search(text):
            continue
        tables = page.extract_tables()
        if not tables:
            continue
        for tbl in tables:
            df = pd.DataFrame(tbl)
            if df.shape[0] >= min_rows and df.shape[1] >= min_cols:
                tables_all.append(df)
    return tables_all


def save_tables_by_title(tables_all, output_root, year, pattern_label):
    grouped_tables = {}
    for df in tables_all:
        title_row = None
        start_row = 0
        for i, val in enumerate(df.iloc[:, 0]):
            if isinstance(val, str) and val.strip().startswith("Table ("):
                title_row = val
                start_row = i
                break
        if not title_row:
            continue
        folder_name, file_name = parse_table_title(title_row)
        if not folder_name:
            continue

        if pattern_label == "hours_worked":
            month_year = extract_month_from_title(title_row)
            if month_year:
                pattern_folder = f"{pattern_label}_{month_year}"
            else:
                pattern_folder = pattern_label
        else:
            pattern_folder = pattern_label

        sub_df = df.iloc[start_row:].reset_index(drop=True)
        key = (folder_name, file_name, pattern_folder)
        grouped_tables.setdefault(key, []).append(sub_df)

    for (
        folder_name,
        file_name,
        pattern_folder,
    ), dfs in grouped_tables.items():
        folder_path = output_root / year / pattern_folder / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        out_path = folder_path / file_name
        final_df = pd.concat(dfs, ignore_index=True)
        final_df.to_csv(
            out_path, index=False, header=False, encoding="utf-8-sig"
        )
        print(
            f"Saved {out_path} with {len(dfs)} parts, {final_df.shape[0]} rows"
        )


if __name__ == "__main__":
    start_time = time.time()
    input_dir = Path.cwd().parents[1] / "data/raw"
    output_root = Path.cwd().parents[1] / "data/interim/interim1"

    pdf_files = list(input_dir.glob("*.pdf"))
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        year = extract_year_from_filename(pdf_file.stem)

        with pdfplumber.open(pdf_file) as pdf:
            appendix_page = find_appendix_page(pdf)
            if appendix_page:
                pr = find_page_range(
                    pdf, appendix_page, skip_pages=250, stop_patterns=PATTERNS
                )
            else:
                pr = None

            if pr:
                print(f"Scanning pages {pr[0]} to {pr[-1]}...")
                for pattern, min_rows, min_cols, label in pattern_shape_list:
                    all_tables = extract_tables(
                        pdf, pr, pattern, min_rows, min_cols
                    )
                    if all_tables:
                        save_tables_by_title(
                            all_tables, output_root, year, label
                        )
            else:
                print("Could not determine a valid page range.")

    elapsed = time.time() - start_time
    print(f"Execution time: {elapsed:.2f} seconds")