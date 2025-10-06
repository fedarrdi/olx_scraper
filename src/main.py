from Extractor import Extractor
def main():
    url = "https://www.olx.bg/ads/q-%D0%B2%D0%BE%D0%BB%D0%B0%D0%BD/"
    extr = Extractor(url)
    extr.get_all_pages_data()
main()