import re
import html
import psycopg
import feedparser
from dateutil import parser
from bs4 import BeautifulSoup
from operator import itemgetter
from utils.config import config
from urllib.parse import urlparse
from utils.helpers import compute_hash


class RSSFeedFetcher:
    def __init__(self, feeds):
        """Initialize with the database configuration details."""
        self.db = config.get_section("database")
        self.schema = config.get_section("schema")
        self.feeds = feeds


    def clean_rss_content(self, raw_html):
        """Extracts text from RSS HTML while removing unnecessary elements."""
        
        # Extract all paragraph content (p tags contain the actual text)
        soup = BeautifulSoup(raw_html, "html.parser")
        paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
        
        # Join paragraphs into a single readable text block
        text = "\n\n".join(paragraphs)  # Keeps paragraph breaks for readability

        # Convert HTML entities (e.g., &nbsp; and &quot;)
        text = html.unescape(text)

        # Remove extra spaces, newlines, and multiple consecutive blank lines
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\n{2,}", "\n\n", text)  # Preserve paragraph separation
        return text.strip()   
     

    def fetch(self):
        """Fetch and parse RSS feed data."""
        articles = []
        for url in self.feeds:
            feed = feedparser.parse(url)
            source = getattr(feed.feed, "link", None)

            # Loop through every feed entry and add data to a dict
            for entry in feed.entries:
                data = {}

                # Check if feed has desired fields (source, pub, hash are exceptions)
                for field in self.schema.keys():
                    if field == "source":
                        # Removing https:// for consistency
                        data["source"] = urlparse(source).netloc

                    if field == "published":
                    # Parse and convert RSS date string into Python datetime object
                        pub = entry.published if hasattr(entry, 'published') else None
                        if pub:
                            try:
                                pub = parser.parse(pub)
                            except Exception as e:
                                print(f"Error parsing date '{pub}': {e}")
                                pub = None
                            data['published'] = pub

                    if field == "content":
                    # If there is full content, extract clean text from HTML
                        if hasattr(entry, 'content'):
                            raw = entry.content[0].value
                            content = self.clean_rss_content(raw)
                        else:
                            content = None
                        data['content'] = content

                    if field not in {"source", "published", "content", "hash"}:
                        # Dynamically extract rest of the fields
                        data[field] = getattr(entry, field, None)

                hash = compute_hash(data['title'], data['source'])
                data['hash'] = hash
                articles.append(data)

        print("RSS feed data fetched successfully.")
        self.store(articles)


    def store(self, articles):
        """
        Inserts RSS articles into PostgreSQL database.
        Prevents duplicate entries using the hash.
        """
        try:
            conn = psycopg.connect(
                dbname = self.db['name'],
                user = self.db['user'],
                password = self.db['pwd'],
                host = self.db['host'],
                port = self.db['port']
            )
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

    feeds = [
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://www.nasa.gov/rss/dyn/breaking_news.rss"
    ]

    fetcher = RSSFeedFetcher(feeds)
    fetcher.fetch()