import logging
import weaviate
import weaviate.classes as wvc
from utils.config import config
from utils.helpers import import_postgres_data


class GenerateEmbeddings:
    def __init__(self, db_conn):
        self.db_conn = db_conn
        self.config = config.get_section("weaviate")

        # Connect to self-hosted Weaviate instance
        self.client = weaviate.connect_to_local(port=self.config["port"])

        # Define collection if it doesn't exist
        self.collection_name = self.config["dbname"]
        if self.collection_name not in self.client.collections.list_all():
            self.create_schema()

    def create_schema(self):
        """Create a Weaviate schema based on config file."""

        # Load schema from config
        schema = [
            wvc.config.Property(
                name=field["name"],
                data_type=wvc.config.DataType(field["dataType"]),
                skip_vectorization=field["skip"],
            )
            for field in self.config["schema"]
        ]

        self.client.collections.create(
            name=self.collection_name,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_contextionary(),
            properties=schema,
        )
        logging.info(f"Created schema for {self.collection_name}")

    def check_postgres(self):
        """
        Check for new articles from PostgreSQL and add them to Weaviate.
        Note: Weaviate expects JSON-compatible values.
        """
        articles = import_postgres_data(
            db_conn=self.db_conn,
            data=self.config["fields"],
            only_new=True,
        )

        if articles:
            collection = self.client.collections.get(self.collection_name)
            with collection.batch.dynamic() as batch:
                for article in articles:
                    data = dict(zip(self.config["fields"], article))

                    # Ensure tags is a list
                    if "tags" in data and isinstance(data["tags"], str):
                        data["tags"] = [tag.strip() for tag in data["tags"].split(",")]

                    # Add object to Weaviate
                    batch.add_object(properties=data)

                    # Mark the PostgreSQL entry as embedded
                    self.mark_as_embedded(data["hash"])

            logging.info("Stored new embeddings.")
            self.client.close()
        else:
            logging.info("No new data to embed.")
            self.client.close()

    def mark_as_embedded(self, hash):
        """Update PostgreSQL table to reflect when an entry has been embedded."""
        cursor = self.db_conn.cursor()
        cursor.execute("UPDATE articles SET embedded = TRUE WHERE hash = %s", (hash,))
        self.db_conn.commit()
        cursor.close()
        logging.info("Embeddings marked in postgreSQL.")
