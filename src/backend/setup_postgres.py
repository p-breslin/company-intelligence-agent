import psycopg

# PostgreSQL connection details
DB_NAME = "cia" # Company Intelligence Agent
DB_USER = "testuser" # Change to a username of choice
DB_PASSWORD = "testpwd" # Change to a password of choice
DB_HOST = "localhost"
DB_PORT = "5432" # Default PostgreSQL port
SUPERUSER = "peter" # Change to a superuser of choice

def setup():
    """
    Creates a PostgreSQL user and database if they do not already exist.
    Assumes the PostgreSQL server is running, the user has superuser privileges, and the user superuser does not require a password.
    """
    try:
        # First connect as superuser ('postgres')
        conn = psycopg.connect(
            dbname = "postgres",  # Default database
            user = f"{SUPERUSER}",
            host = DB_HOST,
            port = DB_PORT
        )
        conn.autocommit = True # Ensures SQL commands take effect immediately
        cur = conn.cursor()

        # Check if the user exists
        cur.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{DB_USER}';")
        user_exists = cur.fetchone()

        # Create the user if not exists
        if not user_exists:
            cur.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';")
            cur.execute(f"ALTER USER {DB_USER} CREATEDB;")  # Grant DB creation rights
            print(f"User '{DB_USER}' created successfully.")
        else:
            print(f"User '{DB_USER}' already exists.")

        # Check if the database exists
        cur.execute(f"""
            SELECT EXISTS (
                SELECT FROM pg_database WHERE datname = '{DB_NAME}'
            );
        """)
        db_exists = cur.fetchone()[0]

        # Create the database if not exists
        if not db_exists:
            cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")
            print(f"Database '{DB_NAME}' created and assigned to '{DB_USER}'.")
        else:
            print(f"Database '{DB_NAME}' already exists.")

        # Closing the cursor and connection frees up resources
        cur.close()
        conn.close()

        # Now create the table, if user and database were created successfully
        create_table()

    except Exception as e:
        print("Error setting up User and Database:", e)


def create_table():
    """Creates the 'articles' table for storing content inside the database."""
    try:
        # Connect to the newly created database
        conn = psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
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
                    hash TEXT UNIQUE NOT NULL,
                    summary TEXT,
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
    setup()