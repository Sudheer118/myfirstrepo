from pathlib import Path
import re
import pandas as pd
import pdfplumber

input_dir = Path.cwd().parents[1] / "data" / "raw"
output_dir = Path.cwd().parents[1] / "data" / "interim" / "parsed_pdfs"
output_dir.mkdir(parents=True, exist_ok=True)

pattern = re.compile(r"\bstatewise\b|\bstate\b", flags=re.IGNORECASE)

for file_path in input_dir.iterdir():
    if file_path.suffix.lower() == ".pdf":
        output_path = output_dir / (file_path.stem + ".csv")

        print(f"Processing {file_path.name}...")

        tables_list = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    for table in tables:
                        df = pd.DataFrame(table)

                        # Normalize multi-line cell text
                        df = df.map(
                            lambda x: " ".join(str(x).split()) if x else x
                        )

                        # Keep only tables that contain "State" or "Statewise"
                        if df.apply(
                            lambda row: row.astype(str).str.contains(pattern)
                        ).any().any():
                            tables_list.append(df)

            if tables_list:
                final_df = pd.concat(tables_list, ignore_index=True)
                final_df.to_csv(output_path, index=False, header=False)
                print(f"Saved: {output_path}")
            else:
                print(f"No matching tables found in {file_path.name}, skipping.")

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

print("All files processed.")
