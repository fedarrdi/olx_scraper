# OLX.bg Car Scraper

A Python web scraper that extracts car listings from OLX.bg, collecting price, title, and direct links, then saving results to a timestamped CSV file.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd olx_scraper

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Requirements

- Python 3.7+
- `requests` -- HTTP requests
- `beautifulsoup4` -- HTML parsing
- `pytest` -- testing

## Usage

```bash
cd src
python main.py
```

You will be prompted to enter an OLX.bg search URL. Press Enter to use the default example URL. The scraper will process all pages automatically with a 10-second delay between requests and save the output to a CSV file in the current directory.

### Output

CSV files are saved as `olx_extract_YYYY-MM-DD_HH-MM-SS.csv` with the following columns:

| Column | Description |
|--------|-------------|
| Price | Listing price |
| Product/Title | Cleaned ad title |
| Ad_URL | Direct link to the ad |
| Source_URL | Original search URL |
| Extracted_At | Extraction timestamp |

## Scripts

### `main.py`

Entry point. Displays a welcome banner, prompts the user for an OLX.bg search URL, and runs the scraper.

### `extractor.py`

Core scraping module containing the `Extractor` class. Handles:

- Fetching and parsing HTML pages
- Detecting pagination and building page URLs
- Extracting price, title, and ad URL from each listing
- Skipping ads with missing price or title
- Saving collected data to CSV

### `test_extractor.py`

Unit tests for the `Extractor` class using pytest. Covers price extraction, title cleaning, URL fallback logic, ad skipping, and CSV output.

```bash
# Run tests
cd src
pytest test_extractor.py -v
```
