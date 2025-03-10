import os
import shutil
import chromadb
from utils.config import config


def clear_chroma(cfg):
    """Deletes the Chroma database."""
    try:
        # Deletes everything inside the folder
        if os.path.exists(cfg["root"]):
            shutil.rmtree(cfg["root"])
            print("ChromaDB storage deleted successfully.")
        else:
            print("ChromaDB storage folder not found.")

    except Exception as e:
        print(f"An error occurred while deleting ChromaDB storage: {e}")


def list_collections(cfg):
    """
    Lists all collections in ChromaDB.
    Trying to connect to a client creates a new database; first check it's existence.
    """
    if not os.path.exists(cfg["root"]):
        print("No collection to list.")
        return

    client = chromadb.PersistentClient(path=cfg["root"])
    collections = client.list_collections()

    if not collections:
        print("No collections found.")
    else:
        print("Existing Collections:")
        for col_name in collections:
            print(f"- {col_name}")


if __name__ == "__main__":
    cfg = config.get_section("chroma")
    clear_chroma(cfg)
    list_collections(cfg)
