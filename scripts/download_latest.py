import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


LANDING_PAGE = "https://www.newcastle.gov.uk/local-government/access-information-and-data/open-data/payments-over-ps250-data-sets"
RAW_DIR = "data/raw"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}

# Regex to extract month + year from messy filenames
MONTH_REGEX = re.compile(
    r"(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-_ ]*(\d{2,4})"
)

def normalise_filename(url: str) -> str:
    """
    Convert messy filenames like:
    - payments-over-250-jan-24.csv
    - Payments_January_2024.csv
    - February 2026.csv
    - 250-payments-2023-11.csv
    into YYYY-MM.csv
    """

    # Decode URL-encoded characters like %20 → space
    filename = unquote(url.split("/")[-1])
    
    # 1. Full month name pattern: "February 2026.csv"
    FULL_MONTH_REGEX = re.compile(
        r"(?i)\b(january|february|march|april|may|june|july|august|september|october|november|december)\b[\s_-]*(\d{4})"
    )
    m_full = FULL_MONTH_REGEX.search(filename)
    if m_full:
        month_str, year_str = m_full.groups()
        month = datetime.strptime(month_str[:3], "%b").month
        year = int(year_str)
        return f"{year}-{month:02d}.csv"

    # 2. Abbreviated month pattern: "jan-24", "sept_2023"
    MONTH_REGEX = re.compile(
        r"(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*[-_ ]*(\d{2,4})"
    )
    m = MONTH_REGEX.search(filename)
    if m:
        month_str, year_str = m.groups()
        month = datetime.strptime(month_str[:3], "%b").month
        year = int(year_str)
        if year < 100:
            year += 2000
        return f"{year}-{month:02d}.csv"

    # 3. Fallback YYYY-MM pattern
    m2 = re.search(r"(\d{4})[-_](\d{2})", filename)
    if m2:
        year, month = m2.groups()
        return f"{year}-{month}.csv"

    # 4. Final fallback
    return f"unknown-{filename}"



def fetch_csv_links():
    session = requests.Session()

    # Retry strategy: 5 retries, exponential backoff
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    session.mount("https://", HTTPAdapter(max_retries=retries))

    r = session.get(LANDING_PAGE, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".csv"):
            links.append(urljoin(LANDING_PAGE, href))

    return links


def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    csv_links = fetch_csv_links()
    existing = set(os.listdir(RAW_DIR))

    for url in csv_links:
        fname = normalise_filename(url)
        if fname in existing:
            continue  # already downloaded

        print(f"Downloading {url} → {fname}")
        data = requests.get(url, headers=HEADERS, timeout=20).content
        with open(os.path.join(RAW_DIR, fname), "wb") as f:
            f.write(data)

if __name__ == "__main__":
    main()
