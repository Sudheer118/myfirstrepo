import pdfplumber
import pandas as pd
from pathlib import Path


# PATHS

pdf_path = Path(__file__).resolve().parents[2] / "data/raw/2023/ISFR_Vol2_2023.pdf"
output_root = Path(__file__).resolve().parents[2] / "data/interim/forest cover/2023"
output_root.mkdir(parents=True, exist_ok=True)



# FIND MATCHING PAGES


matching_pages = []

with pdfplumber.open(pdf_path) as pdf:

    for i, page in enumerate(pdf.pages):

        print(f"Scanning page {i+1}")

        text = page.extract_text()

        if not text:
            continue

        text = text.lower()

        # normalize spaces
        text = " ".join(text.split())

        # normalize hyphen variations
        text = text.replace("district- wise", "district wise")
        text = text.replace("district-wise", "district wise")

        if "district wise forest cover" in text and "scrub" in text:
            matching_pages.append(i + 1)

print("\nMatching pages:", matching_pages)



# DETECT STATE NAME


def get_state_name(text):

    text = text.lower()

    text = text.replace("district- wise", "district wise")
    text = text.replace("district - wise", "district wise")
    text = text.replace("district-wise", "district wise")

    try:
        return (
            text.split("district wise forest cover in")[1]
            .split("\n")[0]
            .strip()
            .title()
        )
    except IndexError:
        return None



# EXTRACT TABLE ROWS


def extract_table_rows(page):

    heading_words = page.search("District Wise Forest Cover", case=False)

    if heading_words:
        top_of_table = heading_words[0]["bottom"] + 5
    else:
        top_of_table = 0

    page_crop = page.crop(
        (20, top_of_table, page.width - 20, page.height - 40)
    )

    words = page_crop.extract_words(
        x_tolerance=3,
        y_tolerance=3,
        keep_blank_chars=False
    )

    if not words:
        return []

    df_words = pd.DataFrame(words)

    df_words["row"] = (df_words["top"] // 12)

    df_words = df_words.sort_values(["row", "x0"])

    rows = []

    for _, group in df_words.groupby("row"):
        rows.append(group.sort_values("x0")["text"].tolist())

    clean_rows = []

    last_district = None

    for row in rows:

        row_values = [str(v).strip() for v in row if pd.notna(v)]

        if not row_values:
            continue

        row_text = " ".join(row_values).lower()

        if "district" in row_text and "calculated" in row_text:
            continue

        district_parts = []
        numeric_part = []

        for i, value in enumerate(row_values):

            clean_value = value.replace(",", "").replace(".", "").replace("-", "")

            is_number = clean_value.isdigit()

            prev_is_text = (
                i > 0 and
                not row_values[i-1].replace(",", "").replace(".", "").replace("-", "").isdigit()
            )

            next_is_text = (
                i < len(row_values) - 1 and
                not row_values[i+1].replace(",", "").replace(".", "").replace("-", "").isdigit()
            )

            # number between words → district name (North 24 Parganas)
            if is_number and prev_is_text and next_is_text:
                district_parts.append(value)

            # normal numeric column
            elif is_number or "." in value or "-" in value:
                numeric_part.append(value)

            else:
                if not numeric_part:
                    district_parts.append(value)
                else:
                    numeric_part.append(value)

        if district_parts:
            district_name = " ".join(district_parts).strip()
            last_district = district_name
        else:
            district_name = last_district

        if len(numeric_part) >= 8 and district_name:

            clean_rows.append([district_name] + numeric_part[:8])

            if district_name.lower() == "grand total":
                break

    return clean_rows


# SAVE FILE


def save_state_table(state, df):

    state_folder = output_root / state
    state_folder.mkdir(exist_ok=True)

    output_path = state_folder / "district_wise_forest_cover.csv"

    df.to_csv(output_path, index=False)

    print("Saved:", output_path)



# MAIN EXTRACTION


state_tables = {}

with pdfplumber.open(pdf_path) as pdf:

    for page_number in matching_pages:

        page = pdf.pages[page_number - 1]

        text = page.extract_text()

        if not text:
            continue

        state = get_state_name(text)

        if state:
            print(f"Page {page_number}: {state}")

        rows = extract_table_rows(page)

        if not rows:
            continue

        columns = [
            "District",
            "Calculated Area by SoI",
            "Very Dense Forest",
            "Mod Dense Forest",
            "Open Forest",
            "Total Forest",
            "% of Area",
            "Change w.r.t 2021",
            "Scrub"
        ]

        df = pd.DataFrame(rows, columns=columns)

        if state in state_tables:

            state_tables[state] = pd.concat(
                [state_tables[state], df],
                ignore_index=True
            )

        else:

            state_tables[state] = df



# SAVE ALL STATES


for state, df in state_tables.items():

    if df.empty:
        continue

    save_state_table(state, df)

print("\nAll states extracted and saved correctly.")