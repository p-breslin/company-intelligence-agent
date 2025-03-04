import logging
import psycopg
from utils.config import config
from utils.helpers import store_to_postgres
from .firecrawl_call import FireCrawlScraper
from backend.weaviate_pipeline import GenerateEmbeddings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


if __name__ == "__main__":
    """
    Unified pipeline for data extraction, storage, and embedding.
    Collects and runs Scraper, SQL storage, and Embedding routines.
    """

    # Connect to PostgreSQL once
    db_user = config.get_section("DB_USER")
    conn = psycopg.connect(**db_user)
    conn.autocommit = True

    try:
        # List of feeds defined in config
        feeds = config.get_list("feeds")

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
