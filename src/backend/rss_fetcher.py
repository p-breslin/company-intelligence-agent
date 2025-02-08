import psycopg
import feedparser
from dateutil import parser
from operator import itemgetter
from utils.config import config
from urllib.parse import urlparse
from utils.helpers import compute_hash, clean_raw_html


class RSSFeedFetcher:
    def __init__(self, feeds):
        """Initialize with the database configuration details."""
        self.db = config.get_section("DB_USER")
        self.schema = config.get_section("schema")
        self.feeds = feeds


    def fetch(self):
        """Fetch and parse RSS feed data."""
        articles = []
        for url in self.feeds:
            feed = feedparser.parse(url)
            source = getattr(feed.feed, "link", None)

            # Loop through every feed entry and add data to a dict
            for entry in feed.entries:
                data = {}

                # Loop over the desired fields in the feed
                for field in self.schema.keys():
                    value = getattr(entry, field, None)

                    if field in {"title", "link", "author", "summary"}:
                        data[field] = clean_raw_html(value, feed="rss") if value and field == "title" else value

                    elif field == "published":
                        try:
                            # Parse and convert RSS date string into Python datetime
                            data[field] = parser.parse(value) if value else None
                        except Exception as e:
                            print(f"Error parsing date '{value}': {e}")
                            data[field] = None

                    elif field == "source":
                        data[field] = urlparse(source).netloc 

                    elif field == "content":
                    # Use cleaned full content if there; otherwise use summary
                        data[field] = clean_raw_html(entry.content[0].value, feed="rss") if hasattr(entry, field) else getattr(entry, "summary", None)

                    elif field == "tags":
                        data[field] = value[0]['term'] if value else None

                    elif field == "hash":
                        data["hash"] = compute_hash(data["title"], data["source"])

                articles.append(data)

        print("RSS feed data fetched successfully.")
        self.store(articles)


    def store(self, articles):
        """
        Inserts RSS articles into PostgreSQL database.
        Prevents duplicate entries using the hash.
        """
        try:
            conn = psycopg.connect(**self.db)
            with conn.cursor() as cur:
                try:
                    # Get column names dynamically from schema
                    columns = list(self.schema.keys())
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
                    getter = itemgetter(*columns) # optimized getter for column order
                    values = [getter(a) for a in articles]
                    cur.executemany(insert_query, values)                    
            
                except Exception as e:
                    print(f"Error inserting article: {e}")
            
            conn.commit()
            conn.close()
            print("RSS data successfully stored in PostgreSQL table.")

        except Exception as e:
            print("Database connection failed:", e)
        

if __name__ == "__main__":
    # fn = "https://www.fierce-network.com/rss/Fierce%20Network%20Homepage/xml"
    feeds = config.get_list("rss_feeds")
    fetcher = RSSFeedFetcher(feeds)
    fetcher.fetch()