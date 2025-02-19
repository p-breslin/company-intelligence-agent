import hashlib
import logging
import feedparser
from dateutil import parser
from utils.config import config
from utils.helpers import clean_html


class RSSHandler:
    def __init__(self, feeds, db_conn):
        """Initialize with the database configuration details."""
        self.schema = config.get_section("schema")
        self.feeds = feeds
        self.incomplete = []  # URLs that need additional scraping
        self.conn = db_conn
        self.cur = self.conn.cursor()

    def fetch(self):
        """Fetch and parse the RSS feed."""
        articles = []
        for url in self.feeds:
            feed = self.parse_rss_feed(url)

            # If URL not RSS feed, mark with domain URL and send to scraper
            if not feed:
                logging.warning(f"Invalid RSS feed: {url}")
                data = {field: None for field in self.schema.keys()}
                data["link"] = url
                self.incomplete.append(url)
                articles.append(data)
                continue

            # Process each entry in the RSS feed
            for entry in feed.entries:
                data = {field: None for field in self.schema.keys()}

                # Get article URL
                link = getattr(entry, "link", None)
                if not link:
                    logging.warning("RSS entry missing link.")
                    continue  # This'll never happen..

                # Generate hash and check for duplicates
                hash = self.generate_hash(link)
                if self.check_hash(hash):
                    logging.info(f"Skipping duplicate: {link}")
                    continue

                # Extract data from feed
                data = self.extract_data(entry, data)

                # Mark as incomplete for scraping if any info is missing
                if any(value is None for value in data.values()):
                    self.incomplete.append(data["link"])

                articles.append(data)

        logging.info(
            f"Fetched {len(articles)} articles. {len(self.incomplete)} need scraping."
        )
        return articles

    def parse_rss_feed(self, url):
        """Parses an RSS feed URL and returns the parsed feed object."""
        try:
            feed = feedparser.parse(url)
            if not getattr(feed.feed, "link", None):
                return None  # Not a valid RSS feed
            return feed
        except Exception as e:
            logging.error(f"Error parsing RSS feed {url}: {e}")
            return None

    def generate_hash(self, link):
        """Generates an MD5 hash for a given link (webpage URL)."""
        return hashlib.md5(link.encode("utf-8")).hexdigest() if link else None

    def extract_data(self, entry, data):
        """Extracts relevant data from an RSS entry."""

        # Loop through data fields as defined in config
        for field in self.schema.keys():

            # Skip embedded (bool for embedding), and link + hash (already done)
            if field in {"embedded", "link", "hash"}:
                continue

            # Title, summary, published, content, tags
            value = getattr(entry, field, None)

            if field in {"title", "summary"}:
                data[field] = clean_html(value, feed="rss") if value else None

            elif field == "published":
                try:
                    # Parse + convert RSS date str into datetime obj
                    data[field] = parser.parse(value) if value else None
                except Exception as e:
                    logging.warning(f"Error parsing date '{value}': {e}")

            elif field == "content":
                if hasattr(entry, "content"):
                    data[field] = clean_html(entry.content[0].value, feed="rss")
                else:
                    # Mark for scraping
                    data[field] = None

            elif field == "tags":
                if value:
                    # E.g. first tag would be value[0]["term"]
                    data[field] = ", ".join(
                        tag["term"] for tag in value if "term" in tag
                    )
                else:
                    data[field] = None

        return data

    def check_hash(self, hash):
        """Checks if the given hash already exists in the postgres database."""
        self.cur.execute("SELECT 1 FROM articles WHERE hash = %s LIMIT 1", (hash,))
        return self.cur.fetchone() is not None
