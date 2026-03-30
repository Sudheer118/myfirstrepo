#This script downloads the raw pdfs
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path


# CONFIG

BASE = "https://desagri.gov.in"
AJAX = f"{BASE}/wp-admin/admin-ajax.php"
URL  = f"{BASE}/document-report-category/agriculture-wages-in-india/"

OUT_DIR = Path(__file__).resolve().parents[2] / "data/raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SKIP_PREFIXES = ("ann", "om")
SKIP_CONTAINS = ("modified-final-manucript-2019-20",)


# SESSION

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
})


# UTILITIES

def get_year_ids(page_url):
    r = session.get(page_url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    return [
        opt["value"]
        for opt in soup.select("#year_filter_sess option")
        if opt.get("value")
    ]

def fetch_year_html(year_id):
    payload = {
        "action": "yearFilter",
        "year_sess_catId": year_id,
        "cat_id": 39,
        "tax_id": "document-report-category",
    }

    r = session.post(
        AJAX,
        data=payload,
        headers={"Referer": URL},
        timeout=30,
    )
    r.raise_for_status()
    return r.text

def extract_pdf_from_post(post_url):
    r = session.get(post_url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    a = soup.select_one("a[href$='.pdf']")
    return urljoin(BASE, a["href"]) if a else None

def download_pdf(pdf_url):
    filename = Path(pdf_url).name
    filename_lc = filename.lower()

    if filename_lc.startswith(SKIP_PREFIXES):
        return

    if any(s in filename_lc for s in SKIP_CONTAINS):
        return

    file_path = OUT_DIR / filename
    if file_path.exists():
        return

    with session.get(pdf_url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with file_path.open("wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)

    print("Downloaded:", filename)


# PROCESS PAGE

def process_page():
    print("Downloading Agriculture Wages data")
    year_ids = get_year_ids(URL)

    for year_id in year_ids:
        html = fetch_year_html(year_id)
        soup = BeautifulSoup(html, "html.parser")

        # Direct PDF links
        for a in soup.select("a[href$='.pdf']"):
            download_pdf(urljoin(BASE, a["href"]))

        # PDFs inside document pages
        for a in soup.select("a[href]"):
            if "/document-report/" in a["href"]:
                pdf_url = extract_pdf_from_post(urljoin(BASE, a["href"]))
                if pdf_url:
                    download_pdf(pdf_url)


# RUN

process_page()
print("DATA DOWNLOAD COMPLETED")
