import psycopg
from utils.config import config
from psycopg import OperationalError

"""Simple script to delete a PostgreSQL database and user."""

try:
    # Import the database configuration details
    db = config.get_section('DB_USER')

    # First connect as superuser ('postgres')
    conn = psycopg.connect(**config.get_section('DB_SUPER'))
    conn.autocommit = True 
    cur = conn.cursor()

    # Cannot drop a database if there are active connections to it.
    # Terminate active connections to the database before dropping it
    cur.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = %s;
    """, (db['dbname'],))
    
    # Drop the database
    cur.execute(f"DROP DATABASE IF EXISTS {db['dbname']};")
    print(f"Database '{db['dbname']}' dropped successfully.")

    # Drop the user
    cur.execute(f"DROP USER IF EXISTS {db['user']};")
    print(f"User '{db['user']}' dropped successfully.")

    conn.commit()
    cur.close()
    conn.close()

except OperationalError as e:
    print(f"OperationalError: {e}")
except Exception as e:
    print("Error during deletion process:", e)