import psycopg
import feedparser
from dateutil import parser
from utils.config import config

class RSSFeedFetcher:
    def __init__(self, feeds):
        """Initialize with the database configuration details."""
        self.db = config.get_section("database")
        self.feeds = feeds

    def fetch(self):
        """Fetch and parse RSS feed data."""
        articles = []
        for url in self.feeds:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Check if feed has desired fields
                title = entry.title if hasattr(entry, 'title') else None
                link = entry.link if hasattr(entry, 'link') else None
                published = entry.published if hasattr(entry, 'published') else None

                # Parse and convert RSS date string into Python datetime object
                if published:
                    try:
                        published = parser.parse(published)
                    except Exception as e:
                        print(f"Error parsing date '{published}': {e}")
                        published = None
        
                articles.append((title, link, published))

        print("RSS feed data fetched successfully.")
        self.store(articles)

    def store(self, articles):
        """Insert RSS articles into PostgreSQL database."""
        try:
            conn = psycopg.connect(
                dbname = self.db['name'],
                user = self.db['user'],
                password = self.db['pwd'],
                host = self.db['host'],
                port = self.db['port']
            )
            
            with conn.cursor() as cur:
                for article in articles:
                    title, link, published = article
                    try:
                        # ON CONFLICT (link) DO NOTHING prevents duplicate entries
                        cur.execute(
                            """
                            INSERT INTO articles (title, link, published)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (link) DO NOTHING;
                            """,
                            (title, link, published)
                        )
                    except Exception as e:
                        print(f"Error inserting article: {e}")
            
            conn.commit()
            conn.close()
            print("RSS data successfully stored in PostgreSQL table.")

        except Exception as e:
            print("Database connection failed:", e)
        

if __name__ == "__main__":

    feeds = [
    "https://www.nasa.gov/rss/dyn/breaking_news.rss"
    ]

    fetcher = RSSFeedFetcher(feeds)
    fetcher.fetch()