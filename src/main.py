from extractor import Extractor


if __name__ == "__main__":
    print("=" * 60)
    print("     WELCOME TO OLX.BG CAR SCRAPER")
    print("=" * 60)
    print()
    print("This tool scrapes car listings from OLX.bg.")
    print("It extracts:")
    print("   • Price")
    print("   • Title (cleaned – no extra newlines)")
    print("   • Direct link to each ad")
    print()
    print("Features:")
    print("   • Skips ads without a price")
    print("   • Saves everything to a timestamped CSV file")
    print("   • Polite delay (10 seconds between pages)")
    print()
    print("Example URL for Volkswagen cars:")
    print("https://www.olx.bg/avtomobili-karavani-lodki/avtomobili-dzhipove/volkswagen/q-автомобили/")
    print("-" * 60)
    print()

    user_url = input("Paste your OLX.bg search URL here (or press Enter to use the Volkswagen example): ").strip()

    if not user_url:
        user_url = "https://www.olx.bg/avtomobili-karavani-lodki/avtomobili-dzhipove/volkswagen/q-%D0%B0%D0%B2%D1%82%D0%BE%D0%BC%D0%BE%D0%B1%D0%B8%D0%BB%D0%B8/"
        print(f"Using default example URL: {user_url}")
    else:
        print(f"Using your URL: {user_url}")

    print("\nStarting scraping... (this may take a while depending on the number of pages)\n")

    extr = Extractor(user_url)
    extr.get_all_pages_data()
