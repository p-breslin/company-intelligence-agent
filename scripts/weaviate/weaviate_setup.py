import logging
import weaviate
import weaviate.classes as wvc
from utils.config import config

cfg = config.get_section("weaviate")
client = weaviate.connect_to_local(port=cfg["port"])

try:
    # Delete all schemas (which deletes all data)
    client.collections.delete_all()
    print("Weaviate database erased successfully.")

    try:
        # Create new Weaviate database
        schema = [
            wvc.config.Property(
                name=field["name"],
                data_type=wvc.config.DataType(field["dataType"]),
                skip_vectorization=field["skip"],
            )
            for field in cfg["schema"]
        ]

        client.collections.create(
            name=cfg["dbname"],
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_contextionary(),
            properties=schema,
        )
        print(f"Created schema for {cfg['dbname']}")

    except Exception as e:
        logging.error(f"Error creating database: {e}")
except Exception as e:
    logging.error(f"Error deleting database: {e}")

finally:
    client.close()
