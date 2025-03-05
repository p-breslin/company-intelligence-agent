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
config = ConfigLoader("config").get_section("arango")

try:
    # Connect to ArangoDB server
    client = ArangoClient(hosts=f"http://localhost:{config['port']}")

    try:
        # Authenticate with root user (required to manage databases)
        sys_db = client.db("_system", username="root", password=os.getenv("ARANGO_PWD"))

        # Create the database if it does not exist
        if not sys_db.has_database(config["dbname"]):
            sys_db.create_database(config["dbname"])
            logging.info(f"Database '{config['dbname']}' created.")
        else:
            logging.info(f"Database '{config['dbname']}' already exists.")

        try:
            # Connect to the database
            db = client.db(
                config["dbname"], username="root", password=os.getenv("ARANGO_PWD")
            )

            # Create collections if they don’t exist
            for c in config["collections"]:
                if not db.has_collection(c):
                    db.create_collection(c)
                    logging.info(f"Collection '{c}' created.")
                else:
                    logging.info(f"Collection '{c}' already exists.")

            # Create an Edge Collection for relationships (if needed)
            if not db.has_collection("Relationships"):
                db.create_collection("Relationships", edge=True)
                logging.info("Edge collection 'Relationships' created.")

            logging.info("ArangoDB initialization complete!")

        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise

    except Exception as e:
        logging.error(f"Failed to authenticate with root: {e}")
        raise

except Exception as e:
    logging.error(f"Failed to connect to ArangoDB server: {e}")
    raise
