import pdfplumber
import pandas as pd
from pathlib import Path



# Extract State Name

def extract_state_name(page):

    header_crop = page.crop((0, 0, page.width, 140))
    header_words = header_crop.extract_words()

    if not header_words:
        return None, None

    df_header = pd.DataFrame(header_words)

    min_top = df_header["top"].min()
    first_line = df_header[df_header["top"] < min_top + 6]
    first_line = first_line.sort_values("x0")

    header_text = " ".join(first_line["text"].tolist())

    if "india state of forest report" in header_text.lower():
        parts = header_text.split(")")
        header_text = parts[-1] if len(parts) > 1 else header_text

    state_name = header_text.strip()

    if not state_name:
        return None, None

    state_display = state_name.title()
    state_key = state_display.lower()

    return state_display, state_key



# Extract Raw Table Rows

def extract_table_rows(page):

    words = page.extract_words(x_tolerance=3, y_tolerance=3)

    if not words:
        return []

    df_words = pd.DataFrame(words)

    df_words["row"] = (df_words["top"] // 8)
    df_words = df_words.sort_values(["row", "x0"])

    rows = []

    for _, group in df_words.groupby("row"):
        row_text = group.sort_values("x0")["text"].tolist()
        rows.append(row_text)

    return rows



# Clean Extracted Rows

def clean_rows(rows):

    clean_rows = []

    for row in rows:

        numeric = []
        text_part = []

        for val in row:

            val_clean = val.replace(",", "").strip()

            # Handle 1. 2. 12.
            if val_clean.endswith("."):
                val_clean = val_clean[:-1]

            if val_clean.isdigit():
                numeric.append(val_clean)
            else:
                text_part.append(val)

        # Handle merged SL No cases
        if len(numeric) == 2 and len(text_part) > 0:
            first_text = text_part[0].replace(".", "")
            if first_text.isdigit():
                numeric.insert(0, first_text)
                text_part = text_part[1:]

        if len(numeric) >= 3:

            slno = numeric[0]
            val_2022 = numeric[1]
            val_2023 = numeric[2]

            district = " ".join(text_part).strip()

            if district == "":
                continue

            clean_rows.append([
                slno,
                district,
                val_2022,
                val_2023
            ])

    return clean_rows



# Process PDF

def process_pdf(pdf_path):

    state_tables = {}

    with pdfplumber.open(pdf_path) as pdf:

        for page_no, page in enumerate(pdf.pages, start=1):

            text_raw = page.extract_text()

            if not text_raw:
                continue

            text_norm = " ".join(text_raw.lower().split())

            if "district-wise number of forest fire detected" not in text_norm:
                continue

            if "snpp-viirs detection" not in text_norm:
                continue

            state_display, state_key = extract_state_name(page)

            if not state_display:
                continue

            print(f"Processing Page {page_no} → {state_display}")

            rows = extract_table_rows(page)

            clean_data = clean_rows(rows)

            if not clean_data:
                print("No rows extracted on page:", page_no)
                continue

            df = pd.DataFrame(clean_data, columns=[
                "Sl No",
                "District",
                "SNPP_VIIRS_2022_23",
                "SNPP_VIIRS_2023_24"
            ])

            df["Sl No"] = pd.to_numeric(df["Sl No"], errors="coerce")
            df["SNPP_VIIRS_2022_23"] = pd.to_numeric(df["SNPP_VIIRS_2022_23"], errors="coerce")
            df["SNPP_VIIRS_2023_24"] = pd.to_numeric(df["SNPP_VIIRS_2023_24"], errors="coerce")

            df = df.dropna(subset=["Sl No", "District"])

            # Merge multi-page tables
            if state_key in state_tables:

                state_tables[state_key]["data"] = pd.concat(
                    [state_tables[state_key]["data"], df],
                    ignore_index=True
                )

            else:

                state_tables[state_key] = {
                    "display_name": state_display,
                    "data": df
                }

    return state_tables



# Save Results

def save_results(state_tables, output_root):

    for state_key, content in state_tables.items():

        df = content["data"]
        state = content["display_name"]

        if df.empty:
            continue

        df = df.drop_duplicates().sort_values("Sl No").reset_index(drop=True)
        df["Sl No"] = df.index + 1

        invalid_chars = '<>:"/\\|?*'
        for ch in invalid_chars:
            state = state.replace(ch, "")

        state_folder = output_root / state
        state_folder.mkdir(parents=True, exist_ok=True)

        output_path = state_folder / "district_wise_forest_fire.csv"

        df.to_csv(output_path, index=False)

    print("\nForest fire tables extracted and saved correctly.")



# MAIN FUNCTION

def main():

    
    pdf_path = Path(__file__).resolve().parents[2] / "data/raw/2023/ISFR_Vol2_2023.pdf"
    output_root = Path(__file__).resolve().parents[2] / "data/interim/fire/2023"

    output_root.mkdir(parents=True, exist_ok=True)

    state_tables = process_pdf(pdf_path)

    save_results(state_tables, output_root)


# Run Script

if __name__ == "__main__":
    main()