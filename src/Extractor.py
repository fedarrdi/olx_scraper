import requests
import re
import time
import csv
from datetime import datetime
from bs4 import BeautifulSoup, Tag
from typing import Optional, List, Iterable, Dict, Any


class Extractor:
    def __init__(self, url: str) -> None:
        """Initialize the extractor with the base URL."""
        self.url = url
        self.data: List[Dict[str, Any]] = []  # Collect all listings here

    def get_web_page_content(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch page content as text. Returns HTML string or None on error."""
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def beautify_html(self, data: str) -> str:
        """Return prettified version of the HTML string."""
        soup = BeautifulSoup(data, "html.parser")
        return soup.prettify()

    def find_by_class(self, html_data: str, class_name: str, tag: Optional[str] = None) -> List[Tag]:
        """Find all elements with the given class (and optional tag)."""
        soup = BeautifulSoup(html_data, "html.parser")
        if tag:
            return soup.find_all(tag, class_=class_name)
        return soup.find_all(class_=class_name)

    def from_el_to_str(self, elements: Iterable[Tag]) -> str:
        """Convert BS4 elements to combined HTML string."""
        return "".join(str(el) for el in elements)

    def last_page_number(self, s: str) -> Optional[int]:
        """Extract highest page number from pagination text."""
        matches = re.findall(r'\bPage\s+(\d+)', s)
        return int(matches[-1]) if matches else None

    def extract_page_count(self, html: str) -> Optional[int]:
        """Extract total page count from pagination."""
        elements = self.find_by_class(html, "pagination-list")
        if not elements:
            print("No pagination-list found. Assuming 1 page.")
            return 1
        combined = self.from_el_to_str(elements)
        return self.last_page_number(combined) or 1

    def get_main_page_html(self, url: str) -> Optional[str]:
        """Fetch and prettify main page."""
        raw = self.get_web_page_content(url)
        return self.beautify_html(raw) if raw else None

    def get_all_pages_urls(self) -> List[str]:
        """Generate URLs for all pages."""
        html_data = self.get_main_page_html(self.url)
        if not html_data:
            return []

        page_count = self.extract_page_count(html_data)
        return [f"{self.url}?page={i}" for i in range(1, page_count + 1)]

    def get_price(self, ad_soup: BeautifulSoup) -> str:
        """Extract price using direct soup search."""
        price_el = ad_soup.find("p", {"data-testid": "ad-price"})
        return price_el.get_text(strip=True) if price_el else "N/A"

    def get_product(self, ad_soup: BeautifulSoup) -> str:
        """Extract title/product name. All newlines are replaced with single spaces."""
        title_el = ad_soup.find(["h4", "h6"], class_=re.compile(r"css-"))  # flexible class match
        if not title_el:
            return "N/A"
        
        # Use space as separator and collapse multiple spaces/newlines
        raw_text = title_el.get_text(separator=" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', raw_text).strip()
        return clean_text

    def get_ad_url(self, ad_soup: BeautifulSoup) -> str:
        """Extract the full URL to the individual ad page."""
        # Primary: look for <a> with href matching OLX ad pattern (/d/ad/ or /d/oferta/)
        link_el = ad_soup.find("a", href=re.compile(r"/d/(ad|oferta)/"))
        if link_el and 'href' in link_el.attrs:
            href = link_el['href'].strip()
            if href.startswith("http"):
                return href
            return f"https://www.olx.bg{href}"

        # Fallback: first <a> with href containing 'ID' (common in OLX ad URLs)
        link_el = ad_soup.find("a", href=re.compile(r"ID"))
        if link_el and 'href' in link_el.attrs:
            href = link_el['href'].strip()
            if href.startswith("http"):
                return href
            return f"https://www.olx.bg{href}"

        # Ultimate fallback
        link_el = ad_soup.find("a", href=True)
        if link_el:
            href = link_el['href'].strip()
            if href.startswith("http"):
                return href
            return f"https://www.olx.bg{href}"

        return "N/A"

    def extract_information_from_page(self, html: Optional[str]) -> None:
        """Extract listings from one page, print + store in memory."""
        if not html:
            return

        main_soup = BeautifulSoup(html, "html.parser")
        listings = main_soup.find_all(class_="css-1sw7q4x")  # ad card class

        if not listings:
            print("No listings found on this page.")
            return

        for idx, listing in enumerate(listings, 1):
            ad_soup = BeautifulSoup(str(listing), "html.parser")

            price    = self.get_price(ad_soup)
            product  = self.get_product(ad_soup)
            ad_url   = self.get_ad_url(ad_soup)

            if price == "N/A" or product == "N/A":
                continue

            # Print to console
            print(price)
            print("\n")
            print(product)
            print(ad_url)
            print("=" * 150)

            # Store in list
            self.data.append({
                "Price": price,
                "Product/Title": product,
                "Ad_URL": ad_url,
                "Source_URL": self.url,
                "Extracted_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    def save_to_csv(self, filename: Optional[str] = None) -> None:
        """Save all collected data to CSV."""
        if not self.data:
            print("No data to save.")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"olx_extract_{timestamp}.csv"

        headers = ["Price", "Product/Title", "Ad_URL", "Source_URL", "Extracted_At"]

        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(self.data)
            print(f"\nData saved successfully to: {filename}")
            print(f"Total listings saved: {len(self.data)}")
        except Exception as e:
            print(f"Error saving CSV: {e}")

    def get_all_pages_data(self) -> None:
        """Fetch all pages, extract data, print, and save to CSV at the end."""
        urls = self.get_all_pages_urls()
        if not urls:
            print("No pages to process.")
            return

        print("Pages to scrape:", urls)

        for i, url in enumerate(urls, 1):
            print(f"\nScraping page {i}/{len(urls)}: {url}")
            html = self.get_web_page_content(url)
            if html:
                self.extract_information_from_page(html)
            time.sleep(10)  # polite delay

        # After all pages → save
        self.save_to_csv()
