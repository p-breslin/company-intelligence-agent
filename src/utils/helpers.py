import re
import html
import hashlib
import psycopg
from bs4 import BeautifulSoup
from operator import itemgetter
from utils.config import config
from urllib.parse import urlparse, urlunparse


def compute_hash(title, url):
    """Hashes title + base domain; ensures consistency across RSS & scraping."""
    base_domain = urlparse(url).netloc  # Extracts the domain
    return hashlib.md5((title + base_domain).encode("utf-8")).hexdigest()


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


def store_to_postgres(articles, db_conn):
    """
    Inserts RSS articles into PostgreSQL database.
    Prevents duplicate entries using the hash.
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

            # Execute query dynamically
            getter = itemgetter(*columns)  # optimized getter for column order
            values = [getter(a) for a in articles]
            cur.executemany(insert_query, values)
            db_conn.commit()
            print(f"{len(values)} articles stored in PostgreSQL table.")

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
        print(columns)

    query = f"SELECT {columns} FROM articles"
    if only_new:
        query += " WHERE embedded IS FALSE"

    cursor.execute(query)
    articles = cursor.fetchall()  # list of tuples (each one is a database row)
    cursor.close()
    print("Articles imported from postgreSQL database.")
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
