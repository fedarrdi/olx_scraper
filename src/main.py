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


def main():
    url = "https://www.olx.bg/ads/q-%D1%81%D0%BF%D0%BE%D1%80%D0%B5%D0%BD%D1%82-%%D0B2%D0%BE%D0%BB%D0%B0%D0%BD/"
    raw_data = get_web_page_content(url)
    data = beautify_html(raw_data)
    file_name = "beutiful_html.html"
    write_in_data_in_file(data, file_name)


main()