# Backend - Company Intelligence Agent

This directory contains the backend code for the Company Intelligence Agent. The backend is responsible for content extraction, web scraping, RSS feed handling, and local LLM processing.

## Structure

```
backend/
│── init.py
│── data_extraction.py          # Orchestrates the data extraction and storage
│── async_rss_handler.py        # Handles RSS feed parsing and data retrieval
│── async_web_scraper.py        # Web scraper for extracting data from target sites if required
|—— embedding_pipeline.py       # Creates and stores vector embeddings in ChromaDB
│── LLM_integration.py          # Handles interactions with the local LLM
```

## Key Components

### 1. **Data Extraction (`data_extraction.py`)**

- Coordinates the data retrieval process.
- Stores clean, standardized data in the postgreSQL database, and vectorized embeddings in the ChrombaDB database by orchestrating `async_rss_handler.py`, `async_web_scraper.py`, and `embedding_pipeline.py`.

### 2. **RSS Handling (`async_rss_handler.py`)**

- Fetches and parses RSS feeds.
- Extracts article content and metadata like publication date, source, and category hints.

### 3. **Web Scraping (`async_web_scraper.py`)**

- Attempts to scrape any content not obtained by the RSS handler.

### 4. **Embedding Storage (`embedding_pipeline.py`)**

- Creates and stores vector embeddings in the ChromaDB database.

### 5. **LLM Integration (`LLM_integration.py`)**

- Handles interactions with the local Large Language Model.
- Uses ChrombaDB embeddings efficient querying (similarity search).
- Provides response generation based on structured knowledge (pre-defined prompts).
