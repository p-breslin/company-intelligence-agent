import chromadb
from utils.config import config


def setup():
    """Initializes a persistent ChromaDB collection for storing embeddings."""
    cfg = config.get_section("chroma")
    client = chromadb.PersistentClient(path=cfg["root"])

    # Creates a collection for storing the embeddings
    collection = client.get_or_create_collection(name=cfg["dbname"])

    print("ChromaDB initialized successfully.")
    return collection


if __name__ == "__main__":
    setup()
