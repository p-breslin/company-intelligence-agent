import chromadb
from datetime import datetime
from utils.config import config 
from utils.helpers import load_postgres_data


class GenerateEmbeddings:
    def __init__(self, custom=False):
        self.chroma = config.get_section("chroma")
        self.custom = custom
        if custom:
            from sentence_transformers import SentenceTransformer
            self.model1 = "all-MiniLM-L6-v2"  # For fast retrieval
            self.model2 = "multi-qa-MiniLM-L6-cos-v1"  # For re-ranking
            self.retrieval_model = SentenceTransformer(self.model1)
            self.ranking_model = SentenceTransformer(self.model2)
    

    def generate_embeddings(self, text):
        """Generates embeddings for retrieval and re-ranking models."""
        fast_emb = self.retrieval_model.encode(text).tolist()
        rank_emb = self.ranking_model.encode(text).tolist()
        return fast_emb, rank_emb


    def store_embeddings(self):
        """Stores embeddings of the postgreSQL data in the ChromaDB database."""
        client = chromadb.PersistentClient(path=self.chroma["root"])
        collection = client.get_or_create_collection(name=self.chroma["dbname"])

        # Load desired data from database by specifying the columns
        articles = load_postgres_data(self.chroma["data"])      

        for article in articles:
            data = dict(zip(self.chroma["data"], article))

            # ChromaDB doesn’t support certain dtypes in metadata
            # Must ensure all metadata values are converted to strings
            metadata_dict = {}
            for key in self.chroma["metadata"]:
                if key in data:
                    value = data[key]
                    if isinstance(value, (list, dict, tuple, set, bytes)):
                        value = str(value)

                    # Convert datetime to ISO 8601 format (YYYY-MM-DD HH:MM:SS)
                    elif isinstance(value, datetime):
                        value = value.isoformat()
                    metadata_dict[key] = value

            if self.custom:
                # Generate custom embeddings
                fast_emb, rank_emb = self.generate_embeddings(data["content"])

                # Store the collection for the retrieval embedding
                collection.add(
                    ids=[f"{data['hash']}_retrieval"],
                    embeddings=[fast_emb],
                    documents=[data["content"]],
                    metadatas=[metadata_dict | {"model": self.model1}]
                )
                # Store the collection for the re-ranking embedding
                collection.add(
                    ids=[f"{data['hash']}_ranking"],
                    embeddings=[rank_emb],
                    documents=[data["content"]],
                    metadatas=[metadata_dict | {"model": self.model2}]
                    )
            else:
                # Store the collection using default embedding model (all-MiniLM-L6-v2)
                collection.add(
                    ids=[f"{data['hash']}"],
                    documents=[data["content"]],
                    metadatas=[metadata_dict]
                    )
        print(f"Stored embeddings.")


if __name__ == "__main__":
    embeddings = GenerateEmbeddings()
    embeddings.store_embeddings()