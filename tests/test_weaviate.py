import weaviate
from utils.config import config

config = config.get_section("weaviate")
client = weaviate.connect_to_local(port=8080)
print(client.is_ready())

articles = client.collections.get(config["dbname"])
response = articles.query.near_text(
    query="How much has QuEra Computing raised in financing", limit=2
)

try:
    for obj in response.objects:
        print(obj.properties["title"])

finally:
    client.close()
