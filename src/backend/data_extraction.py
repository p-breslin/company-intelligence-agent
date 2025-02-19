import psycopg
from utils.config import config
from backend.async_rss_handler import RSSHandler
from backend.async_web_scraper import AsyncScraper
from backend.embedding_pipeline import GenerateEmbeddings
from utils.helpers import store_to_postgres


# Debug
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s - %(message)s",
)


if __name__ == "__main__":
    """
    Unified pipeline for data extraction, storage, and embedding.
    Collects and runs RSS, Scraper, and Embedding routines.
    """

    # Connect to PostgreSQL once
    db_user = config.get_section("DB_USER")
    conn = psycopg.connect(**db_user)
    conn.autocommit = True

    try:
        # RSS handler
        feeds = config.get_list("feeds")

        ## For working example, use this feed:
        rss_handler = RSSHandler([feeds[1]], db_conn=conn)

        # rss_handler = RSSHandler([feeds[3]], db_conn=conn)
        # rss_handler = RSSHandler(["https://www.nasa.gov/news-release/"], db_conn=conn)
        articles = rss_handler.fetch()

        # Activate scraper if there is incomplete data
        if rss_handler.incomplete:
            scraper = AsyncScraper(rss_handler.incomplete)
            scraper.async_scrape(articles)

        # Save to postgreSQL database
        store_to_postgres(articles, db_conn=conn)

        # Generate and store embeddings to ChromaDB
        embeddings = GenerateEmbeddings(db_conn=conn)
        embeddings.check_postgres()

    finally:
        conn.close()
