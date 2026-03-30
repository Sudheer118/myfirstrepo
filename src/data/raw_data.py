import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import re

BASE_URL = "https://dbtdacfw.gov.in/DashboardScheme.aspx?Type=scheme"
HEADERS = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()


def get_hidden(soup):
    return {
        tag["id"]: tag.get("value", "")
        for tag in soup.select("#__VIEWSTATE, #__VIEWSTATEGENERATOR, #__EVENTVALIDATION")
    }


def postback(url, soup, href):
    """Handles ASP.NET postback click events using regex (safer)."""
    match = re.search(r"__doPostBack\('(.+?)','(.*?)'\)", href)
    if not match:
        return None, None
    target, argument = match.groups()

    data = get_hidden(soup)
    data["__EVENTTARGET"], data["__EVENTARGUMENT"] = target, argument

    r = session.post(url, data=data, headers=HEADERS)
    return r.url, BeautifulSoup(r.text, "html.parser")


def get_years():
    r = session.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    return [
        (opt["value"], opt.text.strip())
        for opt in soup.select("#ContentPlaceHolder1_ddlFinyear option")
        if opt["value"] != "0"
    ]


def load_year_page(year_val):
    r = session.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    data = get_hidden(soup)
    data["ctl00$ContentPlaceHolder1$ddlFinyear"] = year_val
    data["ctl00$ContentPlaceHolder1$btnSearch"] = "Search"
    r2 = session.post(BASE_URL, data=data, headers=HEADERS)
    return BeautifulSoup(r2.text, "html.parser")


def scrape_year(year_val, year_txt, file):
    print(f"\n Year: {year_txt}")
    soup = load_year_page(year_val)

    schemes = [
        (a.text.strip(), a["href"])
        for a in soup.find_all("a")
        if "lkbScheme" in a.get("id", "")
    ]

    header_written = False

    with open(file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        for scheme_name, href in schemes:
            print(f"  → Scheme: {scheme_name}")
            scheme_url, scheme_page = postback(BASE_URL, soup, href)

            state_table = scheme_page.find("table", id="ContentPlaceHolder1_GridView1")
            if not state_table:
                continue

            for a in state_table.find_all("a"):
                state_name = a.text.strip()
                print(f"     - State: {state_name}")

                _, district_page = postback(scheme_url, scheme_page, a["href"])
                district_table = district_page.find("table", id="ContentPlaceHolder1_GridView2")

                if not district_table:
                    continue

                headers = ["Year", "Scheme", "State"] + [
                    h.text.strip() for h in district_table.find_all("th")
                ]

                if not header_written:
                    writer.writerow(headers)
                    header_written = True

                for tr in district_table.find_all("tr")[1:]:
                    vals = [td.text.strip() for td in tr.find_all("td")]
                    if vals:
                        writer.writerow([year_txt, scheme_name, state_name] + vals)


def main():
    output = Path(__file__).resolve().parents[2] / "data/raw"
    output.mkdir(parents=True, exist_ok=True)

    for year_val, year_txt in get_years():
        file = output / f"DBT_{year_txt}.csv"
        scrape_year(year_val, year_txt, file)
        print(f" Saved → {file}")


if __name__ == "__main__":
    main()
