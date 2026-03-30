from pathlib import Path
import requests
from bs4 import BeautifulSoup

# EPFO payroll page
URL = "https://www.epfindia.gov.in/site_en/Estimate_of_Payroll.php"

# Output folder (two levels above current dir)
OUTPUT_FOLDER = (Path.cwd().parents[1] / "data" / "raw")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Start session
session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0 Safari/537.36"
    )
})

# Fetch page
response = session.get(URL, timeout=15)
response.raise_for_status()
soup = BeautifulSoup(response.content, "html.parser")

# Collect payroll PDF links
pdf_links = [
    a["href"].strip()
    for a in soup.find_all("a", href=True)
    if a["href"].strip().lower().endswith(".pdf")
       and "Payroll_Data_EPFO" in a["href"]
]

print(f"Found {len(pdf_links)} Payroll PDFs")

# Download PDFs
for pdf_url in pdf_links:

    # Make absolute URL
    if not pdf_url.startswith("http"):
        pdf_url = requests.compat.urljoin(URL, pdf_url)

    # Output path using pathlib
    file_path = OUTPUT_FOLDER / Path(pdf_url).name

    if file_path.exists():
        print(f"Skipping (already exists): {file_path}")
        continue

    print(f"Downloading: {pdf_url} -> {file_path}")

    try:
        with session.get(pdf_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with file_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Saved: {file_path}")

    except Exception as e:
        print(f"Error downloading {pdf_url}: {e}")

print("All Payroll PDFs downloaded successfully")
