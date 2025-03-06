import logging
import psycopg
from utils.config import config
from utils.helpers import store_to_postgres
from firecrawl_extract import FireCrawlScraper
from backend.weaviate_pipeline import GenerateEmbeddings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def extract_data(feeds):
    """
    Uses feeds passed on from Tavily Search.
    Unified pipeline for data extraction, storage, and embedding.
    Collects and runs Scraper, SQL storage, and Embedding routines.
    Maybe add GraphDB storage here too.
    """

    # Connect to PostgreSQL
    db_user = config.get_section("DB_USER")
    conn = psycopg.connect(**db_user)
    conn.autocommit = True

    try:
        # Firecrawl scraper
        scraper = FireCrawlScraper(feeds)
        articles = scraper.run()

        if not articles:
            logging.warning("No articles were extracted. Exiting.")
        else:
            logging.info(f"Extracted {len(articles)} articles. Storing to database...")

            # Save to postgreSQL database
            store_to_postgres(articles, db_conn=conn)

            # Generate and store embeddings to ChromaDB
            embeddings = GenerateEmbeddings(db_conn=conn)
            embeddings.check_postgres()

    finally:
        conn.close()
