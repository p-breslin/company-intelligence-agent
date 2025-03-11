# Key Components

## 1. **Data Extraction (`simple_extractor.py`)**

- Coordinates the data retrieval process.
- Stores clean, standardized data in the postgreSQL database, and vectorized embeddings in the vector database by orchestrating `rss_handler.py`, `simple_scraper.py`, and the chosen vector embedding pipeline.

## 2. **RSS Handling (`rss_handler.py`)**

- Fetches and parses RSS feeds.
- Extracts article content and metadata like publication date, source, and category hints.

## 3. **Web Scraping (`simple_scraper.py`)**

- Attempts to scrape any content not obtained by the RSS handler.