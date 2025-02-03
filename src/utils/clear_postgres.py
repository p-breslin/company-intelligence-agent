import psycopg

"""Simple script to delete a PostgreSQL database and user."""

DB_NAME = "cia" # Company Intelligence Agent
DB_USER = "testuser" # Change to a username of choice
DB_HOST = "localhost"
DB_PORT = "5432" # Default PostgreSQL port
SUPERUSER = "peter" # Change to a superuser of choice

try:
    # First connect as superuser ('postgres')
    conn = psycopg.connect(
        dbname = "postgres",  # Default database
        user = f"{SUPERUSER}",
        host = DB_HOST,
        port = DB_PORT
    )
    conn.autocommit = True 
    cur = conn.cursor()

    # Cannot drop a database if there are active connections to it.
    # Terminate active connections to the database before dropping it
    cur.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = %s;
    """, (DB_NAME,))
    
    # Drop the database
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    print(f"Database '{DB_NAME}' dropped successfully.")

    # Drop the user
    cur.execute(f"DROP USER IF EXISTS {DB_USER};")
    print(f"User '{DB_USER}' dropped successfully.")

    conn.commit()
    cur.close()
    conn.close()

except Exception as e:
    print("Error during deletion process:", e)