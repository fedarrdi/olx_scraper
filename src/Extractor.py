from bs4 import BeautifulSoup
import requests
import re
import time

class Extractor:

    def __init__(self, url):
        self.url = url

    def get_web_page_content(self, url, timeout=10):
        resp = requests.get(url, timeout=timeout)
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
        
    def get_main_page_html(self, url):
        raw_data = self.get_web_page_content(url)
        data = self.beautify_html(raw_data)
        return data

    def last_page_number(self, s: str):
        matches = re.findall(r'\bPage\s+(\d+)', s)
        return int(matches[-1]) if matches else None
    
    def from_el_to_str(self, elements) -> str:
        combined_html = ""
        for el in elements:
            combined_html += str(el) + "\n"
        return combined_html
        

    def extract_page_count(self, html : str) -> int:
        elements = self.find_by_class(html, "pagination-list")

        if not elements:
            print(f"No elements with class pagination-list found.")
            return
        
        combined_html = self.from_el_to_str(elements)

        return self.last_page_number(combined_html)

    def get_all_pages_urls(self):
        page_urls = []
        html_data = self.get_main_page_html(self.url)
        page_count = self.extract_page_count(html_data)
        for i in range(1, page_count + 1):
            new_url = self.url + "?page=" + str(i)
            page_urls.append(new_url)

        return page_urls
    
    def get_all_pages_data(self):
        urls = self.get_all_pages_urls()
        print(urls)
        for i in range(1, len(urls) + 1):
            time.sleep(10)

            html = self.get_web_page_content(urls[i - 1])
            html_str = html.decode("utf-8")

            self.extract_information_from_page(html_str)

    def extract_information_from_page(self, html):
        elements = self.find_by_class(html, "css-1sw7q4x")

        for el in elements:
            html_str = self.from_el_to_str(el)
           #print(self.beautify_html(html_str))
            self.get_price(html_str)
            print("\n")
            print(self.get_description(html_str))
            print("=" * 150)

    #css-blr5zl
    def get_price(self, post_html : str) -> str:
        price = str(self.find_by_class(post_html, "css-blr5zl", tag="p"))
        
        soup = BeautifulSoup(price, 'html.parser')
        price_element = soup.find('p', {'data-testid': 'ad-price'})
        price_value = price_element.text.strip() if price_element else None
        print(price_value)

    #css-hzlye5
    def get_description(self, post_html : str) -> str:
        desc = str(self.find_by_class(post_html, "css-hzlye5", tag="h4"))
        soup = BeautifulSoup(desc, 'html.parser')
        desc_element = soup.find('h4')
        desc_value = desc_element.text.strip() if desc_element else None
        print(desc_value)
