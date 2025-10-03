from bs4 import BeautifulSoup
import requests
import re

def get_web_page_content(url, timeout=10):
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()  
    return resp.content

def beautify_html(data : str) -> str:
    soup = BeautifulSoup(data, "html.parser")
    return soup.prettify()

def find_by_class(html_data : str, class_name : str, tag=None) -> str:
    soup = BeautifulSoup(html_data, "html.parser")

    if tag:
        return soup.find_all(tag, class_=class_name)
    
    return soup.find_all(class_=class_name)
    
def get_main_page_html(url : str):
    raw_data = get_web_page_content(url)
    data = beautify_html(raw_data)
    return data

def last_page_number(s: str):
    matches = re.findall(r'\bPage\s+(\d+)', s)
    return int(matches[-1]) if matches else None

def extract_page_count(html : str) -> int:
    elements = find_by_class(html, "pagination-list")

    if not elements:
        print(f"No elements with class pagination-list found.")
        return
    
    combined_html = ""
    for el in elements:
        combined_html += str(el) + "\n"

    return last_page_number(combined_html)


def get_all_pages_urls(url, page_count):
    page_urls = []
    for i in range(1, page_count + 1):
        new_url = url + "?page=" + str(i)
        page_urls.append(new_url)

    return page_urls

def main():
    url = "https://www.olx.bg/ads/q-%D0%B2%D0%BE%D0%BB%D0%B0%D0%BD/"

    html_data = get_main_page_html(url)
    page_count = extract_page_count(html_data)
    urls = get_all_pages_urls(url, page_count)   
    print(urls)

main()