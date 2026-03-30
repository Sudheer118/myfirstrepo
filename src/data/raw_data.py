#CODE TO DOWNLOAD 2023 RAW FILE
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# BASE URL


base_url = "https://fsi.nic.in/forest-report-2023"

pdf_path = Path(__file__).resolve().parents[2] / "data/raw"
pdf_path.mkdir(parents=True, exist_ok=True)


# GET YEAR LINKS


response = requests.get(base_url, verify=False)
soup = BeautifulSoup(response.text, "html.parser")

years_data = []

for a_tag in soup.find_all("a", class_="megamenu_a"):

    title = a_tag.get("title", "")

    for year in range(2015, 2024):

        if str(year) in title:

            full_url = urljoin(base_url, a_tag.get("href"))
            years_data.append((year, full_url))

years_data.sort(reverse=True)

print("\nDetected Years:")

for year, link in years_data:
    print(f"Year {year} -> {link}")


# DOWNLOAD VOLUME 2 PDF


for year, link in years_data:

    print(f"\nChecking Year {year}...")

    year_folder = pdf_path / str(year)
    year_folder.mkdir(exist_ok=True)

    year_response = requests.get(link, verify=False)
    year_soup = BeautifulSoup(year_response.text, "html.parser")

    vol2_found = False

    for a_tag in year_soup.find_all("a"):

        img = a_tag.find("img")

        if img:

            src = img.get("src", "").lower()

            if "vol-2" in src:

                pdf_href = a_tag.get("href")

                if pdf_href and pdf_href.lower().endswith(".pdf"):

                    pdf_url = urljoin(link, pdf_href)

                    print("Downloading:", pdf_url)

                    pdf_response = requests.get(pdf_url, verify=False)

                    file_path = year_folder / f"ISFR_Vol2_{year}.pdf"

                    with open(file_path, "wb") as f:
                        f.write(pdf_response.content)

                    print("Saved:", file_path)

                    vol2_found = True
                    break

    if not vol2_found:
        print("Volume 2 PDF not found")