import chromadb
from utils.config import config

def setup():
    """Initializes a persistent ChromaDB collection for storing article embeddings."""
    configs = config.get_section('chroma')
    client = chromadb.PersistentClient(path=configs['root'])

    # Creates a collection for storing the embeddings
    collection = client.get_or_create_collection(name=configs['dbname'])

    print("ChromaDB initialized successfully.")
    return collection

if __name__ == "__main__":
    setup()