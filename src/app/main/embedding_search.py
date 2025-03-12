import logging
import chromadb
import weaviate
from utils.config import config
from app.main.local_LLM import LocalLLM


class EmbeddingSearch:
    def __init__(self, query, database="weaviate"):
        self.LLM = LocalLLM()
        self.results = None
        self.query = query

        # Initialize database client and collection
        self.client = None
        self.database = database
        self.cfg = config.get_section(database)

        if database == "weaviate":
            try:
                self.client = weaviate.connect_to_local(port=self.cfg["port"])
                self.collection = self.client.collections.get(self.cfg["dbname"])
                logging.info("Weaviate initialized successfully.")
            except Exception as e:
                logging.error(f"Weaviate Initialization Failed: {e}")
                self.collection = None

        elif database == "chroma":
            try:
                self.client = chromadb.PersistentClient(path=self.cfg["root"])
                self.collection = self.client.get_or_create_collection(
                    name=self.cfg["dbname"]
                )
                logging.info("ChromaDB initialized successfully.")
            except Exception as e:
                logging.error(f"ChromaDB Initialization Failed: {e}")
                self.collection = None
        else:
            logging.error("Database name not found")
            self.collection = None

    def search(self, N=1):
        """Performs a similarity search on the database."""

        if self.database == "weaviate":
            self.results = self.collection.query.near_text(query=self.query, limit=N)

        elif self.database == "chroma":
            self.results = self.collection.query(
                query_texts=[self.query],
                n_results=N,
                include=["documents", "metadatas"],
            )

    def retrieve_data(self):
        """Extracts the data we want from the embedding search results."""

        if self.database == "weaviate":
            retrieved_data = {}

            # Results are stored in a list of Objects
            for obj in self.results.objects:
                for field in self.cfg["fields"]:
                    retrieved_data[field] = obj.properties[field]
                break

            llm_context = retrieved_data["content"]
            return retrieved_data, llm_context

        if self.database == "chroma":
            # docs is list of strings; metadatas is list of metadata dicts
            docs = self.results.get("documents", [])
            metadatas = self.results.get("metadatas", [])

            # Formatting retrieved data for the output
            retrieved_data = [
                {
                    "content": " ".join(doc) if isinstance(doc, list) else doc,
                    "title": metadata.get("title", "Unknown"),
                    "published": metadata.get("published", "Unknown"),
                    "link": metadata.get("link", "Unknown"),
                    "tags": metadata.get("tags", "Unknown").split(","),
                }
                for doc, metadata_list in zip(docs, metadatas)
                for metadata in (
                    metadata_list
                    if isinstance(metadata_list, list) and metadata_list
                    else [{}]
                )
            ]

            # Combine texts for LLM input (flatten doc lists into one str)
            # There would be multiple docs if query N_results is > 1
            llm_context = "\n".join(
                doc if isinstance(doc, str) else " ".join(doc) for doc in docs
            )

            return retrieved_data[0], llm_context

    def run(self):
        self.search()
        retrieved_data, llm_context = self.retrieve_data()
        self.client.close()
        return retrieved_data, llm_context
