import logging
import psycopg
from utils.config import config
from utils.helpers import store_to_postgres
from backend.weaviate_pipeline import GenerateEmbeddings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def store_data(articles):
    """
    Uses feeds passed on from Tavily Search.
    Unified pipeline for data storage.
    Maybe add GraphDB storage here too.
    """

    # Connect to PostgreSQL
    db_user = config.get_section("DB_USER")
    conn = psycopg.connect(**db_user)
    conn.autocommit = True

    try:
        # Save to postgreSQL database
        store_to_postgres(articles, db_conn=conn)

        # Generate and store embeddings to ChromaDB
        embeddings = GenerateEmbeddings(db_conn=conn)
        embeddings.check_postgres()

    finally:
        conn.close()
