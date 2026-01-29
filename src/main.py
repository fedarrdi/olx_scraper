from Extractor import Extractor

if __name__ == "__main__":
    url = "https://www.olx.bg/avtomobili-karavani-lodki/avtomobili-dzhipove/volkswagen/q-%D0%B0%D0%B2%D1%82%D0%BE%D0%BC%D0%BE%D0%B1%D0%B8%D0%BB%D0%B8/"
    extr = Extractor(url)
    extr.get_all_pages_data()
