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

def write_in_data_in_file(data, file_name : str):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(data)

def find_by_class(html_data : str, class_name : str, tag=None) -> str:
    soup = BeautifulSoup(html_data, "html.parser")

    if tag:
        return soup.find_all(tag, class_=class_name)
    
    return soup.find_all(class_=class_name)

def get_data_from_file(file_name : str):
    with open(file_name, "r", encoding="utf-8") as f:
        data = f.read()
        return data
    
def save_main_page_html(url : str, file_name : str):
    raw_data = get_web_page_content(url)
    data = beautify_html(raw_data)
    write_in_data_in_file(data, file_name)


def last_page_number(s: str):
    matches = re.findall(r'\bPage\s+(\d+)', s)
    return int(matches[-1]) if matches else None

def extract_page_count(file_name : str) -> int:
    html = get_data_from_file(file_name)
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
    file_name_mane_page = "beutiful_html.html"


    save_main_page_html(url, file_name_mane_page)
    page_count = extract_page_count(file_name_mane_page)
    urls = get_all_pages_urls(url, page_count)
   


main()