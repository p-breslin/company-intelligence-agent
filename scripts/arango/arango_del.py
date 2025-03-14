import os
import logging
from dotenv import load_dotenv
from arango import ArangoClient
from utils.config import ConfigLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

# Load environment variables
load_dotenv()
cfg = ConfigLoader("config").get_section("arango")

try:
    # Connect to ArangoDB server
    client = ArangoClient(hosts=f"http://localhost:{cfg['port']}")

    try:
        # Authenticate with root user (required to manage databases)
        sys_db = client.db("_system", username="root", password=os.getenv("ARANGO_PWD"))

        # Check if the database exists, then delete it
        if sys_db.has_database(cfg["dbname"]):
            sys_db.delete_database(cfg["dbname"])
            print(f"Database '{cfg['dbname']}' deleted successfully.")
        else:
            print(f"Database '{cfg['dbname']}' does not exist.")

    except Exception as e:
        logging.error(f"Failed to authenticate with root: {e}")
        raise

except Exception as e:
    logging.error(f"Failed to connect to ArangoDB server: {e}")
    raise
