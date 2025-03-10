import os
import logging
from dotenv import load_dotenv
from arango import ArangoClient
from utils.config import ConfigLoader
from ciaV2.structure_data import StructureData

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

load_dotenv()

# Query LLM and store data
sd = StructureData()
context = ConfigLoader("testsConfig").get_value("company_article")
sd.run(company="Nvidia", context=context)

# View newly stored data
cfg = ConfigLoader("config").get_section("arango")
try:
    client = ArangoClient(hosts=f"http://localhost:{cfg['port']}")
    db = client.db(
        cfg["dbname"],
        username=cfg["user"],
        password=os.getenv("ARANGO_PWD"),
    )
except Exception as e:
    logging.error(f"Failed to connect to ArangoDB: {e}")

# Show all collections
query = """
RETURN COLLECTIONS()
"""
cursor = db.aql.execute(query)
print(f"Collections:\n{list(cursor)}\n")

# List all companies stored (returns all company nodes)
query = """
FOR c IN Companies RETURN c
"""
cursor = db.aql.execute(query)
print(f"Company nodes:\n{list(cursor)}\n")

# List all competitor relationships (returns all edges between companies)
"""
FOR e IN CompetesWith RETURN e
"""
print(f"\nEdges between companies (competitors):\n{list(cursor)}\n")

# List the competitors of Nvidia only
query = """
FOR v, e IN 1..1 OUTBOUND "Companies/nvidia" CompetesWith RETURN v.name
"""
cursor = db.aql.execute(query)
print(f"Competitors of Nvidia:\n{list(cursor)}\n")
