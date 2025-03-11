# App - Company Intelligence Agent

This directory contains the application code for the Company Intelligence Agent. The app is responsible for data extraction, local LLM processing, and embedding management.

## Structure

```
app/
├── ciaV2/                           # New feature in development
|
├── data_extraction/                 # Data extraction components
│   ├── firecrawl_extraction/        # Routines for data extraction via Firecrawl
│   ├── simple_extraction/           # Routines for data extraction via simple web scraping and RSS feeds
│   ├── smart_extraction/            # Routines for data extraction via AI tools
|
├── main/                            # Main application logic
│   ├── chromadb_embeddings.py       # ChromaDB embedding logic
│   ├── embedding_search.py          # Embedding search functionality
│   ├── local_LLM.py                 # Handles interactions with the local LLM
│   ├── weaviate_embeddings.py       # Weaviate embeddings logic
|
├── README.MD
```

## Key Components

### 1. **Data Extraction**

- Different methods of extracting data from online sources. `simple_extraction` contains routines for extracting content from basic web pages using a combination of RSS feeds and rudimentary web scraping tools. `firecrawl_extraction` extracts data via Firecrawl (API key required). `smart_extraction` extracts data using a combination of open-source AI tools.

### 2. **Embedding Storage**

- `chromadb_embeddings.py` creates and stores vector embeddings in the ChromaDB database, while `weaviate_embeddings.py` does so for the Weaviate database. Weaviate is the currently used method for vector storage.

### 3. **LLM Integration (`local_LLM.py`)**

- Handles interactions with the local Large Language Model.
- Uses Weaviate embeddings for efficient querying (similarity search).
- Provides response generation based on structured knowledge (pre-defined prompts).