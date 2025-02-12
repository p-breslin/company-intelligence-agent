# Backend - Company Intelligence Agent

This directory contains the backend code for the Company Intelligence Agent. The backend is responsible for content extraction, web scraping, RSS feed handling, and local LLM processing.

## Structure

```
backend/
│── init.py
│── async_extract_data.py       # Orchestrates data extraction from RSS and web scrapers
│── async_rss_handler.py        # Handles RSS feed parsing and data retrieval
│── async_web_scraper.py        # Web scraper for extracting data from target sites if required
│── LLM_integration.py          # Handles interactions with the local LLM
```

## Key Components

### 1. **Data Extraction (`async_extract_data.py`)**

- Coordinates the data retrieval process.
- Uses `async_rss_handler.py` to fetch RSS feed data.
- Uses `async_web_scraper.py` to scrape structured/unstructured web content if required.
- Stores clean, standardized data in the postgreSQL database.

### 2. **RSS Handling (`async_rss_handler.py`)**

- Fetches and parses RSS feeds.
- Extracts article content and metadata like publication date, source, and category hints.

### 3. **Web Scraping (`async_web_scraper.py`)**

- Attempts to scrape any content not obtained by the RSS handler.

### 4. **LLM Integration (`LLM_integration.py`)**

- Handles interactions with the local Large Language Model.
- Uses ChrombaDB embeddings efficient querying (similarity search).
- Provides response generation based on structured knowledge (pre-defined prompts).
