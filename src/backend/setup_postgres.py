import psycopg
from utils.config import config
from psycopg import OperationalError

class PostgreSQLsetup:
    def __init__(self):
        """Initialize with the database configuration details."""
        self.db = config.get_section("database")

    def setup(self):
        """
        Creates a PostgreSQL user and database if they do not already exist.
        Assumes the PostgreSQL server is running, the user has superuser privileges, and the user superuser does not require a password.
        """
        try:
            # First connect as superuser ('postgres')
            conn = psycopg.connect(
                dbname = "postgres", # Default database
                user = self.db['superuser'],
                host = self.db['host'],
                port = self.db['port']
            )
            conn.autocommit = True # Ensures SQL commands take effect immediately
            cur = conn.cursor()

            # Check if the user exists
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM pg_roles WHERE rolname = '{self.db['user']}'
                );
            """)
            user_exists = cur.fetchone()[0]

            # Create the user with DB creation rights if not exists
            if not user_exists:
                cur.execute(f"CREATE USER {self.db['user']} WITH PASSWORD '{self.db['pwd']}';")
                cur.execute(f"ALTER USER {self.db['user']} CREATEDB;")
                print(f"User '{self.db['user']}' created successfully.")
            else:
                print(f"User '{self.db['user']}' already exists.")

            # Check if the database exists
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM pg_database WHERE datname = '{self.db['name']}'
                );
            """)
            db_exists = cur.fetchone()[0]

            # Create the database if not exists
            if not db_exists:
                cur.execute(f"CREATE DATABASE {self.db['name']} OWNER {self.db['user']};")
                print(f"Database '{self.db['name']}' created and assigned to '{self.db['user']}'.")
            else:
                print(f"Database '{self.db['name']}' already exists.")

            # Closing the cursor and connection frees up resources
            cur.close()
            conn.close()

            # Now create the table, if user and database were created successfully
            self.create_table()

        except OperationalError as e:
            print(f"OperationalError: {e}")
        except Exception as e:
            print("Error setting up User and Database:", e)


    def create_table(self):
        """Creates the 'articles' table for storing content inside the database."""
        try:
            # Connect to the newly created database
            conn = psycopg.connect(
                dbname = self.db['name'],
                user = self.db['user'],
                password = self.db['pwd'],
                host = self.db['host'],
                port = self.db['port']
            )
            cur = conn.cursor()

            # Check if the table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'articles'
                );
            """)
            table_exists = cur.fetchone()[0]

            # Create the table if not exists
            if not table_exists:
                cur.execute("""
                    CREATE TABLE articles (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        link TEXT UNIQUE NOT NULL,
                        source TEXT NOT NULL,
                        summary TEXT,
                        content TEXT,
                        hash TEXT UNIQUE NOT NULL,
                        published TIMESTAMP
                    );
                """)
                conn.commit()
                print("Table 'articles' created successfully.")
            else:
                print("Table 'articles' already exists.")

            cur.close()
            conn.close()
        except Exception as e:
            print("Error creating table:", e)


if __name__ == "__main__":
    db_setup = PostgreSQLsetup()
    db_setup.setup()