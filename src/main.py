from bs4 import BeautifulSoup
import requests

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

def get_data_from_file(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        data = f.read()
        return data
    
def save_main_page_html(url, file_name):
    raw_data = get_web_page_content(url)
    data = beautify_html(raw_data)
    write_in_data_in_file(data, file_name)

def extract_other_pages_links(file_name, class_name):
    data_old = get_data_from_file(file_name)
    print(find_by_class(data_old, class_name))

def main():
    url = "https://www.olx.bg/ads/q-%D0%B2%D0%BE%D0%BB%D0%B0%D0%BD/"
    file_name = "beutiful_html.html"
    save_main_page_html(url, file_name)

    class_name = "pagination-list"
    extract_other_pages_links(file_name, class_name)


main()