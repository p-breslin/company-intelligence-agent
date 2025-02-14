import chromadb
from datetime import datetime
from utils.config import config
from utils.helpers import import_postgres_data


class GenerateEmbeddings:
    def __init__(self, db_conn):
        self.db_conn = db_conn
        self.chroma = config.get_section("chroma")
        client = chromadb.PersistentClient(path=self.chroma["root"])
        self.collection = client.get_or_create_collection(name=self.chroma["dbname"])

    def check_postgres(self):
        # Check for new articles from PostgreSQL (loads them if so)
        articles = import_postgres_data(
            db_conn=self.db_conn, data=self.chroma["data"], only_new=True
        )

        if articles:
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
                        elif isinstance(value, datetime):
                            value = value.isoformat()  # (YYYY-MM-DD HH:MM:SS)
                        metadata_dict[key] = value

                # Store collection with default embedding model (all-MiniLM-L6-v2)
                self.collection.add(
                    ids=[f"{data['hash']}"],
                    documents=[data["content"]],
                    metadatas=[metadata_dict],
                )

                self.mark_as_embedded(data["hash"])
            print("Stored new embeddings.")
        else:
            print("No new data to embed.")

    def mark_as_embedded(self, hash):
        """Update postgres table to reflect when entry has been embedded."""
        cursor = self.db_conn.cursor()
        cursor.execute("UPDATE articles SET embedded = TRUE WHERE hash = %s", (hash,))
        self.db_conn.commit()
        cursor.close()


if __name__ == "__main__":
    embeddings = GenerateEmbeddings()
