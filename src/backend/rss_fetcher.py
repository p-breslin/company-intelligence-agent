import re
import html
import psycopg
import feedparser
from dateutil import parser
from bs4 import BeautifulSoup
from utils.config import config
from urllib.parse import urlparse
from utils.helpers import compute_hash


class RSSFeedFetcher:
    def __init__(self, feeds):
        """Initialize with the database configuration details."""
        self.db = config.get_section("database")
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
            for entry in feed.entries:
                # Check if feed has desired fields
                title = entry.title if hasattr(entry, 'title') else None
                link = entry.link if hasattr(entry, 'link') else None
                source = feed.feed.link if hasattr(feed.feed, 'link') else None
                source = urlparse(source).netloc # Removing https:// for consistency
                summary = entry.summary if hasattr(entry, 'summary') else None
                hash = compute_hash(title, link)
                
                # Parse and convert RSS date string into Python datetime object
                published = entry.published if hasattr(entry, 'published') else None
                if published:
                    try:
                        published = parser.parse(published)
                    except Exception as e:
                        print(f"Error parsing date '{published}': {e}")
                        published = None

                # If there is full content, extract clean text from HTML
                if hasattr(entry, 'content'):
                    raw_html = entry.content[0].value
                    content = self.clean_rss_content(raw_html)
                else:
                    content = None
                
                articles.append({
                    "title": title,
                    "link": link,
                    "source": source,
                    "summary": summary,
                    "content": content,
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
                try:
                    # Prevent duplicate entries using the hash
                    cur.executemany(
                        """
                        INSERT INTO articles (title, link, source, summary, content, hash, published)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (hash) DO NOTHING;
                        """,
                        [(a["title"], a["link"], a["source"], a["summary"], a["content"], a["hash"], a["published"]) for a in articles]
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
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://www.nasa.gov/rss/dyn/breaking_news.rss"
    ]

    fetcher = RSSFeedFetcher(feeds)
    fetcher.fetch()