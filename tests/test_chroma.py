import logging
import chromadb
from utils.config import config

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s - %(message)s",
)


class ChromaDBViewer:
    def __init__(self, limit=1):
        chroma = config.get_section("chroma")
        client = chromadb.PersistentClient(path=chroma["root"])
        self.collection = client.get_or_create_collection(name=chroma["dbname"])
        self.data = self.collection.get(limit=limit)
        logging.debug(f"ChromaDB Root Path: {chroma['root']}")

    def list_collections(self):
        """Gets a list for all stored collections."""
        try:
            for key, value in self.data.items():
                if key == "documents":
                    continue
                print(f"{key}: {value}")
        except Exception as e:
            logging.error(f"No collections found in the ChromaDB database: {e}")

    def query_collection(self, N):
        """
        Vector similarity search using the content embedding.
        Distance metric: smaller distance = more relevant response.
        """
        query = self.collection.query(
            query_texts=["New chip sales record?"], n_results=N
        )
        docs = query.get("documents", [])
        metadatas = query.get("metadatas", [])

        for i, meta in enumerate(metadatas[0]):
            print(f"Title: {meta['title']}\nDistance: {query['distances'][0][i]}\n")

        # Combine texts for LLM input (flatten doc lists into one str)
        # There would be multiple docs if query N_results is > 1
        llm_context = "\n".join(
            doc if isinstance(doc, str) else " ".join(doc) for doc in docs
        )
        print(f"Context for LLM:\n{llm_context[:500]}...")


if __name__ == "__main__":
    viewer = ChromaDBViewer()
    viewer.list_collections()
    viewer.query_collection(N=3)
