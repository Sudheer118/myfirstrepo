from pathlib import Path
import pdfplumber
import pandas as pd

def extract_tables(pdf_path: Path) -> list[pd.DataFrame]:
    """Extract all tables from a given PDF and return a list of DataFrames."""
    tables_list = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                for table in page_tables:
                    df = pd.DataFrame(table).dropna(how="all")

                    #  Handle multi-line cells (no warning)
                    df = df.map(lambda x: x.replace("\n", " ").strip() if isinstance(x, str) else x)

                    if not df.empty:
                        tables_list.append(df)
    except Exception as e:
        print(f"Error reading {pdf_path.name}: {e}")
    return tables_list


def combine_and_save(tables: list[pd.DataFrame], output_path: Path):
    """Combine all tables and save as a single CSV file."""
    if not tables:
        print(f"No tables to save for {output_path.stem}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined = pd.concat(tables, ignore_index=True)
    combined.to_csv(output_path, index=False, header=False)
    print(f"Saved: {output_path}")


def process_pdf(pdf_path: Path, output_root: Path, input_root: Path):
    print(f"Processing: {pdf_path.name}")
    tables = extract_tables(pdf_path)
    relative_path = pdf_path.parent.relative_to(input_root)
    output_dir = output_root / relative_path
    output_csv = output_dir / f"{pdf_path.stem}.csv"
    combine_and_save(tables, output_csv)


def run_pipeline(input_root: Path, output_root: Path):
    print(f"Starting PDF to CSV extraction pipeline...")
    print(f"Input directory : {input_root}")
    print(f"Output directory: {output_root}\n")

    pdf_files = list(input_root.rglob("*.pdf"))
    if not pdf_files:
        print("No PDF files found.")
        return

    for pdf_file in pdf_files:
        process_pdf(pdf_file, output_root, input_root)

    print("\nAll PDFs processed successfully.")


if __name__ == "__main__":
    input_root = Path(__file__).resolve().parents[2]/("data/raw")
    output_root = Path(__file__).resolve().parents[2]/("data/interim")
    run_pipeline(input_root, output_root)
