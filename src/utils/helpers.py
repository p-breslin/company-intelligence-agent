import re
import html
import hashlib
import logging
from bs4 import BeautifulSoup
from utils.config import config
from urllib.parse import urlparse, urlunparse


def generate_hash(link):
    """Generates an MD5 hash for a given link (webpage URL)."""
    return hashlib.md5(link.encode("utf-8")).hexdigest() if link else None


def check_hash(cur, hashes):
    """Checks if hash(es) exists in the PostgreSQL database."""
    if not hashes:
        return set()  # always return a set

    # Batch check if many hashes
    if len(hashes) > 1:
        placeholders = ", ".join(["%s"] * len(hashes))
        query = f"SELECT hash FROM articles WHERE hash IN ({placeholders})"
        cur.execute(query, tuple(hashes))
        return {row[0] for row in cur.fetchall()}

    # Single hash check
    else:
        hash = next(iter(hashes))  # hashes is passed as dict_values
        cur.execute("SELECT 1 FROM articles WHERE hash = %s LIMIT 1", (hash,))
        result = cur.fetchone()
        return {result[0]} if result else set()


def clean_html(raw_html, feed="rss"):
    """Extracts text from raw HTML and removes unnecessary elements."""

    # Remove HTML entities (ellipses handled at the end)
    raw_html = html.unescape(raw_html)

    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(raw_html, "html.parser")

    if feed == "rss":
        # Preserve paragraph breaks
        text = "\n\n".join(soup.stripped_strings)

    elif feed == "web":
        # Use spaces instead of newlines for better readability
        text = soup.get_text(separator=" ")

    else:
        text = soup.get(text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Replace ellipses with a clear indicator
    text = text.replace("[&#8230;]", "(content truncated).")
    text = text.replace("[…]", "(content truncated).")

    return text


def convert_rss(rss_list):
    """Converts an RSS feed URL to the standard website domain."""
    converted = []
    for rss_url in rss_list:
        parsed_url = urlparse(rss_url)

        # Remove known RSS-related path elements
        path_elems = r"(/?(rss|feed|feeds|index\.rss|rss\.xml|atom\.xml)(/.*)?)$"
        new_path = re.sub(path_elems, "", parsed_url.path, flags=re.IGNORECASE)

        # Handle common feed subdomains like "feeds.website.com"
        domain = parsed_url.netloc
        if domain.startswith("feeds."):
            domain = domain.replace("feeds.", "", 1)

        # Reconstruct the URL with new components
        website = urlunparse((parsed_url.scheme, domain, new_path, "", "", ""))
        converted.append(website.rstrip("/"))  # Remove trailing slashes
        print(website.rstrip("/"))

    return converted


def validate_article(article, schema):
    """
    Ensures an article contains all required fields.
    If a field is missing, it is added with a default value.
    """
    # Create a copy to avoid modifying the original
    validated_article = article.copy()

    for field in schema:
        if field not in validated_article:
            validated_article[field] = "not found"

    return validated_article


def store_to_postgres(articles, db_conn):
    """
    Inserts RSS articles into PostgreSQL database.
    Prevents duplicate entries using the hash.
    Skips and logs articles with missing columns.
    """
    try:
        cur = db_conn.cursor()
        try:
            # Get column names dynamically from schema
            columns = list(config.get_section("schema").keys())

            # If embedded is in columns w/o a value, PostgreSQL will error
            if "embedded" in columns:
                columns.remove("embedded")

            # Create placeholders for values
            placeholders = ", ".join(["%s"] * len(columns))
            # Join column names for SQL query
            col_names = ", ".join(columns)

            # Construct dynamic INSERT statement
            insert_query = f"""
                INSERT INTO articles ({col_names})
                VALUES ({placeholders})
                ON CONFLICT (hash) DO NOTHING;
            """

            # Ensure every article has the correct fields
            articles = [validate_article(article, columns) for article in articles]

            # Extract values dynamically
            values = [
                [article.get(col, "not found") for col in columns]
                for article in articles
            ]

            # Insert into the database
            cur.executemany(insert_query, values)
            db_conn.commit()
            logging.info(f"{len(values)} articles stored in PostgreSQL.")

        except Exception as e:
            db_conn.rollback()  # Rollback the transaction on error
            print(f"Error inserting article: {e}")

        finally:
            cur.close()

    except Exception as e:
        print("Database connection failed:", e)


def import_postgres_data(db_conn, data="all", only_new=False):
    """
    Loads data (defined by the columns) stored in PostgreSQL database.
    only_new: if True, loads only articles that haven't been embedded.
    """
    cursor = db_conn.cursor()

    if data == "all":
        columns = "*"
    else:
        # Ensure 'embedded' column is included for filtering
        if "embedded" not in data:
            data.append("embedded")
        columns = ", ".join(data)

    query = f"SELECT {columns} FROM articles"
    if only_new:
        query += " WHERE embedded IS FALSE"

    cursor.execute(query)
    articles = cursor.fetchall()  # list of tuples (each one is a database row)
    cursor.close()
    logging.info("Articles imported from postgreSQL database.")
    return articles


def token_count(text):
    """
    Estimates the token count based on word and character length.
        - Approx. number of tokens per word in English = 0.75.
        - Average number of characters per token = 4.
        - If text has many short words: (characters/4) gives better estimate.
        - If text has longer words: (words*0.75) is more accurate.
    """
    words = text.split()
    chars = len(text)
    return int(max(len(words) * 0.75, chars / 4))
