import feedparser
from dateutil import parser
from utils.config import config
from urllib.parse import urlparse
from utils.helpers import compute_hash, clean_html, store_to_postgres


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
                # Initialize with None values for all database fields
                data = {field: None for field in self.schema.keys()}

                # Loop over the desired fields in the feed
                for field in self.schema.keys():
                    value = getattr(entry, field, None)

                    if field in {"title", "link", "author", "summary"}:
                        data[field] = clean_html(value, feed="rss") if value and field == "title" else value

                    elif field == "published":
                        try:
                            # Parse and convert RSS date string into Python datetime
                            data[field] = parser.parse(value) if value else None
                        except Exception as e:
                            print(f"Error parsing date '{value}': {e}")

                    elif field == "source":
                        data[field] = urlparse(source).netloc 

                    elif field == "content":
                    # Use cleaned full content if there; otherwise use summary
                        data[field] = clean_html(entry.content[0].value, feed="rss") if hasattr(entry, field) else getattr(entry, "summary", None)

                    elif field == "tags":
                        data[field] = value[0]['term'] if value else None

                    elif field == "hash":
                        data["hash"] = compute_hash(data["title"], data["source"])

                articles.append(data)
        print("RSS feed data fetched successfully.")
        store_to_postgres(articles)
        

if __name__ == "__main__":
    # fn = "https://www.fierce-network.com/rss/Fierce%20Network%20Homepage/xml"
    feeds = config.get_list("rss_feeds")
    fetcher = RSSFeedFetcher(feeds)
    fetcher.fetch()