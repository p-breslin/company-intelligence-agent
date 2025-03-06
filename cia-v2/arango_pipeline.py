import os
import logging
from dotenv import load_dotenv
from arango import ArangoClient
from utils.config import ConfigLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

load_dotenv()


class GraphDBHandler:
    def __init__(self):
        config = ConfigLoader("config").get_section("arango")
        try:
            client = ArangoClient(hosts=f"http://localhost:{config['port']}")
            self.db = client.db(
                config["dbname"],
                username=config["user"],
                password=os.getenv("ARANGO_PWD"),
            )
        except Exception as e:
            logging.error(f"Failed to connect to ArangoDB: {e}")

        # Vertex and Edge collections
        self.articles = self.db.collection("Articles")
        self.companies = self.db.collection("Companies")
        self.products = self.db.collection("Products")
        self.produces = self.db.collection("Produces")
        self.competes = self.db.collection("CompetesWith")

    def insert_company(self, company_name):
        key = company_name.lower().replace(" ", "_")
        if not self.db.collection("Companies").has(key):
            self.companies.insert({"_key": key, "name": company_name})
        return key

    def insert_product(self, product_name):
        key = product_name.lower().replace(" ", "_")
        if not self.db.collection("Products").has(key):
            self.products.insert({"_key": key, "name": product_name})
        return key

    def create_relationship(self, collection, from_id, to_id):
        self.db.collection(collection).insert({"_from": from_id, "_to": to_id})
