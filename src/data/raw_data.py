from urllib.parse import urljoin, urlparse
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import urllib3

# Disable HTTPS certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def make_session() -> requests.Session:
    """Create a configured requests session."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0 Safari/537.36"
        )
    })
    return session


def filename_from_url(url: str) -> str:
    """Extract filename from URL."""
    return Path(urlparse(url).path).name or "download.pdf"


def get_pdf_links(session: requests.Session, page_url: str) -> list[dict]:
    """Extract PDF links categorized by 'Overall', 'State', and 'Bank'."""
    print(f"Fetching page: {page_url}")
    resp = session.get(page_url, timeout=30, verify=False)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href.lower().endswith(".pdf"):
            continue

        full_url = urljoin(page_url, href)
        href_lower = href.lower()

        if "overall" in href_lower:
            category = "Overall"
        elif "state" in href_lower:
            category = "State"
        elif "bank" in href_lower:
            category = "Bank"
        else:
            continue

        links.append({"url": full_url, "category": category})

    print(f"Found {len(links)} PDF links.")
    return links


def download_pdfs(session: requests.Session, links: list[dict], data_dir: Path):
    """Download PDFs into subfolders by category."""
    for item in links:
        url = item["url"]
        category = item["category"]

        category_dir = data_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        filepath = category_dir / filename_from_url(url)

        if filepath.exists():
            print(f"Skipped (exists): {filepath.name}")
            continue

        print(f"Downloading: {filepath.name}")
        try:
            with session.get(url, stream=True, timeout=60, verify=False) as r:
                r.raise_for_status()
                with filepath.open("wb") as f:
                    for chunk in r.iter_content(1024 * 64):
                        if chunk:
                            f.write(chunk)
            print(f"Saved: {filepath}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {filepath.name}: {e}")


if __name__ == "__main__":
    print("Starting Mudra PDF scraping pipeline...")

    base_url = "https://www.mudra.org.in"
    page_url = f"{base_url}/Home/ShowPDF"
    output_path = Path(__file__).resolve().parents[2]
    data_dir = output_path / "data" / "raw"
    
    data_dir.mkdir(parents=True, exist_ok=True)

    session = make_session()
    pdf_links = get_pdf_links(session, page_url)
    download_pdfs(session, pdf_links, data_dir)

    print("All PDFs downloaded and organized successfully!")
