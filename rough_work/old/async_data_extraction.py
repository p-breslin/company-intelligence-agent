import asyncio
import aiohttp
import feedparser
from dateutil import parser
from bs4 import BeautifulSoup
from utils.config import config
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from utils.helpers import compute_hash, clean_html


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


    async def single_scrape(self, session, url, article):
        """Scrapes a single article asynchronously."""
        headers = {"User-Agent": "Mozilla/5.0"}
        source = urlparse(url).netloc

        # Respect robots.txt
        permission, delay = self.respect_robots(source)
        if not permission:
            # print(f"Skipping {url} as per robots.txt")
            # continue
            print("You are not respecting robots.txt...")
        await asyncio.sleep(delay)  # Respect crawl delay

        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    print(f"Failed to fetch {url} - Status Code: {response.status}")
                    return url, None

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Extract title if missing
                if not article["title"]:
                    title_tag = soup.find("title")
                    article["title"] = title_tag.text.strip() if title_tag else None

                # Extract published date if missing
                if not article["published"]:
                    date_selectors = [
                        {"property": "article:published_time"},
                        {"property": "og:updated_time"},
                        {"name": "date"},
                        {"property": "publish_date"},
                    ]
                    for meta_tag in date_selectors:
                        tag = soup.find("meta", meta_tag)
                        if tag and tag.get("content"):
                            try:
                                date = parser.parse(tag["content"])
                            except Exception as e:
                                print(f"Error parsing date '{tag['content']}': {e}")
                            break

                # Extract content if missing
                if not article["content"]:
                    content_tag = soup.find("article")
                    article["content"] = clean_html(content_tag.text.strip(), feed="web") if content_tag else None

                # Extract summary if missing
                if not article["summary"]:
                    meta_tags = [
                        {"name": "description"}, {"property": "og:description"}
                        ]
                    for meta in meta_tags:
                        tag = soup.find("meta", meta)
                        if tag and "content" in tag.attrs:
                            article["summary"] = tag["content"]
                            break

                # Extract tags if missing (TO-DO: ML CLASSIFIER)
                if not article["tags"]:
                    tag = soup.find("meta", {"name": "keywords"})
                    article["tags"] = tag.get("content") if tag else None

                # Compute hash if missing
                if not article["hash"]:
                    article["hash"] = compute_hash(article.get("title"), article.get("source"))

                # Temporary workaround: if no content, use the summary
                if not article["content"]:
                    article["content"] = article["summary"]

                return url, article

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return url, None


    async def scrape_articles(self, articles):
        """Asyncchronous scraping for multiple articles (all at once)."""
        if not self.incomplete:
            print("No articles need scraping.")
            return []

        print(f"Scraping {len(self.incomplete)} articles asynchronously...")

        tasks = []
        async with aiohttp.ClientSession() as session:
            for url in self.incomplete:
                # Find the relevant article that needs scraping
                article = next((a for a in articles if a["link"] == url), None)
                if article:
                    tasks.append(self.single_scrape(session, url, article))

            scraped_results = await asyncio.gather(*tasks)  # Run all tasks in parallel
        return scraped_results  # Returns list of (url, articles) tuples


    def async_scrape(self, articles):
        """Starts async scraping and updates missing content."""
        scraped_data = asyncio.run(self.scrape_articles(articles))  # Run async scraper

        # Merge scraped data back into articles list
        for url, data in scraped_data:
            if data:  # Only update if scrape was successful
                for article in articles:
                    if article["link"] == url:
                        article.update(data)
                        break  # Stop searching once found
        print("Async scraping complete.")

        
if __name__ == "__main__":
    feeds = ["https://www.fierceelectronics.com/rss/xml"]
    # feeds = config.get_list("rss_feeds")
    extractor = ExtractData(feeds)
    articles = extractor.fetch()  # Gather RSS Data

    if extractor.incomplete:  # Scrape if there is incomplete data
        extractor.async_scrape(articles)

    store_to_postgres(articles)