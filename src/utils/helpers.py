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

    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(raw_html, "html.parser")

    if feed == "rss":
        # Preserve paragraph breaks; normalize whitespace; convert HTML entities
        text = "\n\n".join(soup.stripped_strings)
        text = re.sub(r"\s+", " ", html.unescape(text)).strip()

    if feed == "web":
        # Use space instead of newlines for better readability
        text = soup.get_text(separator=" ")
        text = re.sub(r"\s+", " ", text).strip()

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


def store_to_postgres(articles):
    """
    Inserts RSS articles into PostgreSQL database.
    Prevents duplicate entries using the hash.
    """
    try:
        conn = psycopg.connect(**config.get_section("DB_USER"))
        with conn.cursor() as cur:
            try:
                # Get column names dynamically from schema
                columns = list(config.get_section("schema").keys())
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

            except Exception as e:
                print(f"Error inserting article: {e}")

        conn.commit()
        conn.close()
        print("Data successfully stored in PostgreSQL table.")

    except Exception as e:
        print("Database connection failed:", e)


def load_postgres_data(data="all"):
    """Loads data (defined by the columns) stored in PostgreSQL database."""
    conn = psycopg.connect(**config.get_section("DB_USER"))
    cursor = conn.cursor()

    if data == "all":
        columns = "*"
    else:
        columns = ", ".join(data)

    cursor.execute(f"SELECT {columns} FROM articles;")
    articles = cursor.fetchall()  # list of tuples (each one is a database row)
    cursor.close()
    conn.close()
    print("Articles loaded from postgreSQL database.")
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
