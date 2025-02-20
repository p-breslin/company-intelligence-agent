# Backend - Company Intelligence Agent

This directory contains the backend code for the Company Intelligence Agent. The backend is responsible for content extraction, web scraping, RSS feed handling, and local LLM processing.

## Structure

```
backend/
│── init.py
│── data_extraction.py          # Orchestrates the data extraction and storage
│── rss_handler.py              # Handles RSS feed parsing and data retrieval
│── web_scraper.py              # Web scraper for extracting data from target sites if required
|—— embedding_pipeline.py       # Creates and stores vector embeddings in ChromaDB
│── LLM_integration.py          # Handles interactions with the local LLM
```

## Key Components

### 1. **Data Extraction (`data_extraction.py`)**

- Coordinates the data retrieval process.
- Stores clean, standardized data in the postgreSQL database, and vectorized embeddings in the ChrombaDB database by orchestrating `rss_handler.py`, `web_scraper.py`, and `embedding_pipeline.py`.

### 2. **RSS Handling (`rss_handler.py`)**

- Fetches and parses RSS feeds.
- Extracts article content and metadata like publication date, source, and category hints.

### 3. **Web Scraping (`web_scraper.py`)**

- Attempts to scrape any content not obtained by the RSS handler.

### 4. **Embedding Storage (`embedding_pipeline.py`)**

- Creates and stores vector embeddings in the ChromaDB database.

### 5. **LLM Integration (`LLM_integration.py`)**

- Handles interactions with the local Large Language Model.
- Uses ChrombaDB embeddings efficient querying (similarity search).
- Provides response generation based on structured knowledge (pre-defined prompts).

## Data Extraction Scheduling

**Cron** is a command-line tool that schedules tasks to run automatically at specific times. It is used here as an example scheduling the data extraction tasks so as to have a consistent polling of the online information.

### Cron Setup Instructions

- **Edit your crontab:**
  ```sh
  crontab -e
  ```
- **Add the cron job:**
  ```sh
  0 */6 * * * /path/to/python3 /path/to/data_extraction.py >> /path/to/logfile.log 2>&1
  ```
- Replace `/path/to/python3` and `/path/to/data_extraction.py` with the **absolute paths** on your machine.
- `0 */6 * * *` means the job runs at minute 0, every 6 hours, every day.