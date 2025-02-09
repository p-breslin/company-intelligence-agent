import chromadb
from utils.config import config

class ChromaDBViewer:
    def __init__(self, limit=1):
        chroma = config.get_section("chroma")
        client = chromadb.PersistentClient(path=chroma["root"])
        self.collection = client.get_or_create_collection(name=chroma["dbname"])
        self.data = self.collection.get(limit=limit)

        print(f"ChromaDB Root Path: {chroma['root']}")


    def list_collections(self):
        """Gets a list for all stored collections."""
        if not self.data["ids"]:
            print("No collections found in the ChromaDB database.")
            return 
        for key, value in self.data.items():
            if key == 'documents':
                continue
            print(f"{key}: {value}")


    def query_collection(self):
        """
        Vector similarity search using the content embedding.
        Distance metric: smaller distance = more relevant response.
        """
        query = self.collection.query(query_texts=['New chip sales record?'], n_results=2)
        results = query["metadatas"][0]
        for i, meta in enumerate(results):
            print(f"{meta['title']}\n{query['distances'][0][i]}\n")


if __name__ == "__main__":
    viewer = ChromaDBViewer()
    # viewer.list_collections()
    viewer.query_collection()