import hashlib
import feedparser
from dateutil import parser
from utils.config import config
from urllib.parse import urlparse
from utils.helpers import compute_hash, clean_html


class RSSHandler:
    def __init__(self, feeds):
        """Initialize with the database configuration details."""
        self.schema = config.get_section("schema")
        self.feeds = feeds
        self.incomplete = []  # URLs that need additional scraping

    def fetch(self):
        """Fetch and parse RSS feed data."""
        articles = []
        for url in self.feeds:
            feed = feedparser.parse(url)
            source = getattr(feed.feed, "link", None)
            hash = hashlib.md5((source).encode("utf-8")).hexdigest()

            # Loop through every feed entry and add data to a dict
            for entry in feed.entries:
                # Initialize with None values for all database fields
                data = {field: None for field in self.schema.keys()}

                # Loop over the desired fields in the feed
                for field in self.schema.keys():
                    value = getattr(entry, field, None)

                    if field == "link":
                        data[field] = value

                    if field in {"title", "author", "summary"}:
                        data[field] = clean_html(value, feed="rss")

                    elif field == "published":
                        try:
                            # Parse and convert RSS date str into datetime obj
                            data[field] = parser.parse(value) if value else None
                        except Exception as e:
                            print(f"Error parsing date '{value}': {e}")

                    elif field == "source":
                        data[field] = urlparse(source).netloc

                    elif field == "content":
                        # Use cleaned full content; otherwise mark for scraping
                        if hasattr(entry, field):
                            data[field] = clean_html(entry.content[0].value, feed="rss")
                        else:
                            # Mark for scraping
                            self.incomplete.append(data["link"])

                    elif field == "tags":
                        if value:
                            # Tag 1 would be value[0]["term"]
                            data[field] = ", ".join(
                                tag["term"] for tag in value if "term" in tag
                            )
                        else:
                            data[field] = None

                articles.append(data)
        print(f"RSS feed data fetched. {len(self.incomplete)} articles need scraping.")
        return articles
