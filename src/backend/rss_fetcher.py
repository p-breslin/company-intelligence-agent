import psycopg
import hashlib
import feedparser
from dateutil import parser
from utils.config import config

class RSSFeedFetcher:
    def __init__(self, feeds):
        """Initialize with the database configuration details."""
        self.db = config.get_section("database")
        self.feeds = feeds

    def compute_hash(self, content):
        """Converts url into MD5 hash."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def fetch(self):
        """Fetch and parse RSS feed data."""
        articles = []
        for url in self.feeds:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Check if feed has desired fields
                title = entry.title if hasattr(entry, 'title') else None
                link = entry.link if hasattr(entry, 'link') else None
                source = feed.feed.link if hasattr(feed.feed, 'link') else None
                summary = entry.summary if hasattr(entry, 'summary') else None
                hash = self.compute_hash(title + link)
                
                # Parse and convert RSS date string into Python datetime object
                published = entry.published if hasattr(entry, 'published') else None
                if published:
                    try:
                        published = parser.parse(published)
                    except Exception as e:
                        print(f"Error parsing date '{published}': {e}")
                        published = None
                
                articles.append({
                    "title": title,
                    "link": link,
                    "source": source,
                    "summary": summary,
                    "hash": hash,
                    "published": published
                    })

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
                conflict_count = 0
                for a in articles:
                    try:
                        # Prevent duplicate entries using the hash
                        cur.execute(
                            """
                            INSERT INTO articles (title, link, source, summary, hash, published)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (hash) DO NOTHING;
                            """,
                            (a["title"], a["link"], a["source"], a["summary"], a["hash"], a["published"])

                        )
                        # Detect if a conflict occurred
                        if cur.rowcount == 0:
                            conflict_count += 1
                    except Exception as e:
                        print(f"Error inserting article: {e}")
                print(f"Hash conflicts detected: {conflict_count}")
            
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