from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0 Safari/537.36"
            )
        }
    )
    return session


def get_plfs_annual_report_links(session: requests.Session, page_url: str):
    """Scrape the page for all Annual Report, Periodic Labour Force Survey (PLFS) pdfs."""
    resp = session.get(page_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text()

        if (
            ("Annual Report, Periodic Labour Force Survey" in text)
            or ("annual_report" in href.lower())
            or ("annualreportplfs" in href.lower())
        ):
            if href.lower().endswith(".pdf"):
                full_url = urljoin(page_url, href)
                links.append(full_url)

    links = sorted(set(links), reverse=True)
    return links


def filename_from_url(url: str) -> str:
    path = Path(urlparse(url).path)
    return path.name or "download.pdf"


def download_pdfs(session: requests.Session, links, download_dir: Path):
    download_dir.mkdir(parents=True, exist_ok=True)
    for url in links:
        filename = filename_from_url(url)
        filepath = download_dir / filename
        if filepath.exists():
            print(f"Skipping (already exists): {filename}")
            continue
        print(f"Downloading {filename} from {url}...")
        try:
            with session.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with filepath.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 64):
                        if chunk:
                            f.write(chunk)
            print(f"Saved: {filepath}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {url}: {e}")


if __name__ == "__main__":
    base_url = "https://dge.gov.in/dge/reference-publication-reports-annual"
    data_dir = Path.cwd().parents[1] / "data/raw"

    session = make_session()
    links = get_plfs_annual_report_links(session, base_url)
    print(f"Found {len(links)} PLFS Annual Report links.")
    for link in links:
        print(" ", link)
    download_pdfs(session, links, data_dir)