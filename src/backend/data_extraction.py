import time
import requests
import feedparser
from dateutil import parser
from bs4 import BeautifulSoup
from utils.config import config
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from utils.helpers import compute_hash, clean_html, store_to_postgres


class ExtractData:
    """
    Fetch RSS Feed.
    If no content, send to scraper.
    Scraper should navigate to actual URL of the article.
    """
    def __init__(self, feeds):
        """Initialize with the database configuration details."""
        self.db = config.get_section("DB_USER")
        self.schema = config.get_section("schema")
        self.feeds = feeds
        self.incomplete = []  # URLs that need additional scraping


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
                    # Use cleaned full content if there; otherwise mark for scraping
                        if hasattr(entry, field):
                            data[field] = clean_html(entry.content[0].value, feed="rss")
                        else:
                            self.incomplete.append(data["link"])  # Mark for scraping

                    elif field == "tags":
                        data[field] = value[0]['term'] if value else None

                    elif field == "hash":
                        data["hash"] = compute_hash(data["title"], data["source"])

                articles.append(data)
        print(f"RSS feed data fetched. {len(self.incomplete)} articles need scraping.")
        return articles


    def respect_robots(self, source):
        """
        Determines if scraping is allowed and what the crawl delay is.
        If no delay, still rate limit to avoid getting blocked.
        """
        robots_url = urljoin("https://" + source, "/robots.txt")
        rp = RobotFileParser()
        
        try:
            rp.set_url(robots_url)
            rp.read()
            allowed = rp.can_fetch("*", "https://" + source)  # Check permission
            delay = rp.crawl_delay("*") or 2  # Default delay if not specified
            return allowed, delay
        except Exception as e:
            print(f"Error fetching robots.txt from {source}: {e}")
            return True, 2  # Assume scraping is allowed with default delay


    def scrape(self, articles):
        """Scrapes web page only for a few attributes."""
        headers = {"User-Agent": "Mozilla/5.0"}  # spoofs browser to avoid bot detection

        for url in self.incomplete:
            source = urlparse(url).netloc  # Removing https:// for consistency

            # Get permission and crawl delay in one call
            permission, delay = self.respect_robots(source)
            if not permission:
                # print(f"Skipping {url} as per robots.txt")
                # continue
                print(f"You are not respecting {source} robots.txt...")

            time.sleep(delay)  # Respect the crawl delay before scraping

            try:
                # Retrieve HTML content of the page
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error fetching {url}: {e}")
                continue

            # Parse the HTML content
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the corresponding RSS article that needs scraping
            article = next((a for a in articles if a["link"] == url), None)
            if not article:
                continue

            # Now scrape only the missing fields
            if not article["title"]:
                tag = soup.find("title")
                article["title"] = tag.text.strip() if tag else None

            if not article["published"]:
                # Published date: search for <meta> tags with property
                selectors = [
                    {"property": "article:published_time"},
                    {"property": "og:updated_time"},
                    {"name": "date"},
                    {"property": "publish_date"},
                ]
                for meta_tag in selectors:
                    tag = soup.find("meta", meta_tag)
                    if tag and tag.get("content"):
                        try:
                            article["published"] = parser.parse(tag["content"])
                            break
                        except Exception as e:
                            print(f"Error parsing date '{tag['content']}': {e}")

            if not article["content"]:
                tag = soup.find("article")
                article["content"] = clean_html(tag.text.strip(), feed="web") if tag else None

            if not article["summary"]:
                # Search for summary using description or OpenGraph attributes
                meta_tags = [{"name": "description"}, {"property": "og:description"}]
                for meta in meta_tags:
                    tag = soup.find("meta", meta)
                    if tag and "content" in tag.attrs:
                        article["summary"] = tag["content"]
                        break  # Stop if a valid summary is found  

            if not article["tags"]:
                tag = soup.find("meta", {"name": "keywords"})
                article["tags"] = tag.get("content") if tag else None

            if not article["hash"]:
                # Compute hash for duplication detection
                article["hash"] = compute_hash(article.get("title"), article.get("source"))

            # Temporary workaround; if no content then just set it to the summary
            if not article["content"]:
                article["content"] = article["summary"]

            print("Scraping completed.")
        

if __name__ == "__main__":
    # feeds = ["https://www.fierceelectronics.com/rss/xml"]
    feeds = config.get_list("rss_feeds")
    extractor = ExtractData(feeds)
    articles = extractor.fetch()  # Gather RSS Data

    if extractor.incomplete:  # Scrape if there is incomplete data
        extractor.scrape(articles)

    store_to_postgres(articles)