import logging
import weaviate
from utils.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

cfg = config.get_section("weaviate")

try:
    client = weaviate.connect_to_local(port=cfg["port"])
    logging.info(client.is_ready())

    try:
        articles = client.collections.get(cfg["dbname"])

        try:
            response = articles.query.near_text(
                query="How much has QuEra Computing raised in financing", limit=2
            )

            for obj in response.objects:
                print(obj.properties["title"])
            client.close()

        except Exception as e:
            logging.error(f"Failed to run embedding search: {e}")
            client.close()

    except Exception as e:
        logging.error(f"Failed to obtain collection: {e}")
        client.close()

except Exception as e:
    logging.error(f"Failed to connect to client: {e}")
