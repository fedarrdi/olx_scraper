from bs4 import BeautifulSoup
import requests
import re

class Extractor:

    def __init__(self, url):
        self.url = url

    def get_web_page_content(self, timeout=10):
        resp = requests.get(self.url, timeout=timeout)
        resp.raise_for_status()  
        return resp.content

    def beautify_html(self, data : str) -> str:
        soup = BeautifulSoup(data, "html.parser")
        return soup.prettify()

    def find_by_class(self, html_data : str, class_name : str, tag=None) -> str:
        soup = BeautifulSoup(html_data, "html.parser")

        if tag:
            return soup.find_all(tag, class_=class_name)
        
        return soup.find_all(class_=class_name)
        
    def get_main_page_html(self):
        raw_data = self.get_web_page_content()
        data = self.beautify_html(raw_data)
        return data

    def last_page_number(self, s: str):
        matches = re.findall(r'\bPage\s+(\d+)', s)
        return int(matches[-1]) if matches else None

    def extract_page_count(self, html : str) -> int:
        elements = self.find_by_class(html, "pagination-list")

        if not elements:
            print(f"No elements with class pagination-list found.")
            return
        
        combined_html = ""
        for el in elements:
            combined_html += str(el) + "\n"

        return self.last_page_number(combined_html)


    def get_all_pages_urls(self, page_count):
        page_urls = []
        html_data = self.get_main_page_html()
        page_count = self.extract_page_count(html_data)
        for i in range(1, page_count + 1):
            new_url = self.url + "?page=" + str(i)
            page_urls.append(new_url)

        return page_urls