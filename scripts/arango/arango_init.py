import os
import logging
from dotenv import load_dotenv
from arango import ArangoClient
from utils.config import ConfigLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

"""
ArangoDB supports two types of collections:
1. Document Collection (default): Stores regular JSON-like documents.
2. Edge Collection (edge=True): Specifically designed to store relationships (edges) between documents.
"""

# Load environment variables
load_dotenv()
cfg = ConfigLoader("config").get_section("arango")

try:
    # Connect to ArangoDB server
    client = ArangoClient(hosts=f"http://localhost:{cfg['port']}")

    try:
        # Authenticate with root user (required to manage databases)
        sys_db = client.db("_system", username="root", password=os.getenv("ARANGO_PWD"))

        # Create the database if it does not exist
        if not sys_db.has_database(cfg["dbname"]):
            sys_db.create_database(cfg["dbname"])
            logging.info(f"Database '{cfg['dbname']}' created.")
        else:
            logging.info(f"Database '{cfg['dbname']}' already exists.")

        try:
            # Connect to the database
            db = client.db(
                cfg["dbname"],
                username=cfg["user"],
                password=os.getenv("ARANGO_PWD"),
            )

            # Create vertex and edge collections if they don’t exist
            for v in cfg["vertices"]:
                if not db.has_collection(v):
                    db.create_collection(v)
                    logging.info(f"Vertex collection '{v}' created.")

            for e in cfg["edges"]:
                if not db.has_collection(e):
                    db.create_collection(e, edge=True)
                    logging.info(f"Edge collection '{e}' created.")

                else:
                    logging.info("Collections already exist.")

            logging.info("ArangoDB initialization complete.")

        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise

    except Exception as e:
        logging.error(f"Failed to authenticate with root: {e}")
        raise

except Exception as e:
    logging.error(f"Failed to connect to ArangoDB server: {e}")
    raise
