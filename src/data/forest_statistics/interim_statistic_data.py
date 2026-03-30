import pdfplumber
import pandas as pd
import re
from pathlib import Path

# CONFIG


pdf_path = Path(__file__).resolve().parents[2] / "data/raw/2023/ISFR_Vol2_2023.pdf"
output_root = Path(__file__).resolve().parents[2] / "data/interim/statistics/2023"

output_root.mkdir(parents=True, exist_ok=True)

# FIND MATCHING PAGES

matching_pages = []

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):

        text = page.extract_text()
        if not text:
            continue

        text = " ".join(text.lower().split())

        if "area statistics of the forest types found in" not in text:
            continue

        tables = page.extract_tables()

        for table in tables:
            if not table:
                continue

            header_text = " ".join(
                str(cell)
                for row in table[:2]
                for cell in row
                if cell
            ).lower()

            if "forest type" in header_text:
                matching_pages.append(i + 1)
                break

# EXTRACT STATE NAME

def extract_state_name(text_clean):

    marker = "area statistics of the forest types found in"
    text_lower = text_clean.lower()

    if marker in text_lower:
        after_text = text_lower.split(marker)[1].strip()
        state_name = after_text.split(" (")[0].strip().title()

        for ch in '<>:"/\\|?*':
            state_name = state_name.replace(ch, "")

        return state_name

    return None

# VALIDATE NUMBER

def is_valid_number(value):

    value = value.replace(",", "")
    return bool(re.fullmatch(r"\d+(\.\d+)?", value))

# EXTRACT TABLE

def extract_table_from_page(page):

    words = page.extract_words(x_tolerance=3, y_tolerance=3)

    if not words:
        return None

    df_words = pd.DataFrame(words)

    df_words["top"] = df_words["top"].astype(float)
    df_words["x0"] = df_words["x0"].astype(float)

    df_words["row"] = (df_words["top"] // 12)

    df_words = df_words.sort_values(["row", "x0"])

    all_rows = []
    header_found = False

    for _, group in df_words.groupby("row"):

        row_values = group.sort_values("x0")["text"].tolist()
        row_values = [str(v).strip() for v in row_values if pd.notna(v)]

        if not row_values:
            continue

        row_text = " ".join(row_values)
        row_lower = row_text.lower()

        if "forest fire" in row_lower:
            break

        if "forest types have been classified" in row_lower:
            break

        if "forest type" in row_lower and "area" in row_lower:
            header_found = True
            continue

        if not header_found:
            continue

        if "forest cover map" in row_lower:
            continue

        if row_lower.startswith("forest types have"):
            break

        if len(row_values) < 4:
            continue

        area_candidate = row_values[-2].replace(",", "")
        percent_candidate = row_values[-1].replace(",", "")

        if not is_valid_number(area_candidate):
            continue

        if not is_valid_number(percent_candidate):
            continue

        left_part = row_values[:-2]

        left_part = [
            v for v in left_part
            if not re.fullmatch(r"\d{3}", v)
        ]

        if not left_part:
            continue

        slno = ""
        forest_type = ""

        if re.fullmatch(r"\d{1,2}", left_part[0]):
            slno = left_part[0]
            forest_type = " ".join(left_part[1:])

        elif "total" in " ".join(left_part).lower():
            forest_type = " ".join(left_part)

        else:
            continue

        all_rows.append([
            slno,
            forest_type.strip(),
            float(area_candidate),
            float(percent_candidate)
        ])

    if not all_rows:
        return None

    df = pd.DataFrame(all_rows, columns=[
        "Sl No",
        "Forest Type",
        "Area",
        "% of total mapped area"
    ])

    return df

# PROCESS PDF

def process_pdf(pdf_path, matching_pages):

    state_tables = {}
    current_state = None

    with pdfplumber.open(pdf_path) as pdf:

        for page_number in matching_pages:

            page = pdf.pages[page_number - 1]

            text_raw = page.extract_text()

            if not text_raw:
                continue

            text_clean = " ".join(text_raw.split())
            text_lower = text_clean.lower()

            state_name = extract_state_name(text_clean)

            if state_name:
                current_state = state_name
                print(f"\nProcessing State: {current_state}")

            if current_state is None:
                continue

            if "forest type" not in text_lower or "area" not in text_lower:
                continue

            df = extract_table_from_page(page)

            if df is None:
                continue

            if current_state in state_tables:
                state_tables[current_state] = pd.concat(
                    [state_tables[current_state], df],
                    ignore_index=True
                )
            else:
                state_tables[current_state] = df

    return state_tables

# SAVE FILES

def save_state_files(state_tables):

    for state, df in state_tables.items():

        if df.empty:
            continue

        state_folder = output_root / state
        state_folder.mkdir(parents=True, exist_ok=True)

        output_path = state_folder / "forest_types.csv"

        df.to_csv(output_path, index=False)

        print(f"Saved: {output_path}")

# RUN

state_tables = process_pdf(pdf_path, matching_pages)

save_state_files(state_tables)

print("\nState-wise extraction complete.")