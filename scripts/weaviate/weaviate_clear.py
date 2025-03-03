import weaviate
from utils.config import config

config = config.get_section("weaviate")
client = weaviate.connect_to_local(port=config["port"])

# Delete all schemas (which deletes all data)
try:
    client.collections.delete_all()
    print("Weaviate database erased successfully.")

except Exception as e:
    print(f"Error deleting database: {e}")

finally:
    client.close()
