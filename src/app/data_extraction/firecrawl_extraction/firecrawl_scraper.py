import re
import time
import hashlib
import logging
from typing import Optional, List
from firecrawl import FirecrawlApp
from utils.config import ConfigLoader
from pydantic import BaseModel, Field
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ExtractSchema(BaseModel):
    """Schema for extracting structured article data using Firecrawl."""

    title: Optional[str] = Field(None, description="Title of the article.")
    link: Optional[str] = Field(None, description="URL of the original article.")
    published: Optional[str] = Field(
        None, description="The published date of the article in ISO format."
    )
    summary: Optional[str] = Field(
        None, description="Short summary of the article content."
    )
    content: Optional[str] = Field(
        None, description="Full extracted text of the article."
    )
    tags: Optional[List[str]] = Field(
        None, description="List of keywords or tags related to the article."
    )


class FireCrawlScraper:
    def __init__(self, feeds, db_conn):
        try:
            self.feeds = feeds
            self.cur = db_conn.cursor()

            config = ConfigLoader("API_KEYS")
            api_key = config.get_value("firecrawl")
            if not api_key:
                raise ValueError("API key is missing. Please check config.")
            self.app = FirecrawlApp(api_key=api_key)
        except Exception as e:
            logging.error(f"Failed to initialize Firecrawl: {e}")
            raise

    def generate_hash(self, link):
        """Generates an MD5 hash for a given link (webpage URL)."""
        return hashlib.md5(link.encode("utf-8")).hexdigest() if link else None

    def check_hash(self, hash):
        """Checks if the hash already exists in the PostgreSQL database."""
        self.cur.execute("SELECT 1 FROM articles WHERE hash = %s LIMIT 1", (hash,))
        return self.cur.fetchone() is not None

    def get_links(self, homepage):
        """Extracts all links from the given webpage."""
        try:
            response = self.app.scrape_url(url=homepage, params={"formats": ["links"]})

            # Ensure response structure is correct
            if not response or "links" not in response:
                logging.warning(
                    f"Unexpected response structure when scraping {homepage}: {response}"
                )
                return []

            return response["links"]

        except RequestException as re:
            logging.error(f"Network error while accessing {homepage}: {re}")
        except Exception as e:
            logging.error(f"Unexpected error in function: {e}")
        return []

    def filter_links(self, links, homepage, min_word_count=4):
        """Determines if link is likely an article based on its last segment."""
        filtered = []
        for link in links:
            if not link.startswith(homepage):
                continue

            # Get the last part of the URL
            last_segment = link.rstrip("/").split("/")[-1]

            # Split on hyphens or underscores
            words = re.split(r"[-_]", last_segment)

            # Count words (allowing words with numbers)
            word_count = sum(1 for word in words if re.match(r"^[a-zA-Z0-9]+$", word))

            # Must have at least min_word_count
            if word_count >= min_word_count:
                filtered.append(link)

        return filtered

    def batch_scrape(self, links_w_hashes):
        """Batch scrapes multiple article URLs at once."""
        try:
            if not links_w_hashes:
                return []

            urls = list(links_w_hashes.keys())
            response = self.app.batch_scrape_urls(
                urls=urls,
                params={
                    "formats": ["json"],
                    "jsonOptions": {
                        "schema": ExtractSchema.model_json_schema(),
                    },
                },
            )

            if not response.get("data", []):
                logging.warning(f"Unexpected batch scrape response: {response}")
                return []

            # Extract article data from each batch item + attach hash
            articles = []
            for item in response.get("data", []):
                if "json" in item:
                    article_data = item["json"]
                    url = article_data.get("link")
                    article_data["hash"] = links_w_hashes[url]
                    articles.append(article_data)

            return articles

        except RequestException as re:
            logging.error(f"Network error during batch scraping: {re}")
        except Exception as e:
            logging.error(f"Unexpected error in function: {e}")

        return []

    def batch_scrape_async(self, links_w_hashes):
        """Asynchronously batch scraping."""
        try:
            if not links_w_hashes:
                return []

            urls = list(links_w_hashes.keys())
            logging.info(f"Starting async batch scrape for {len(urls)} URLs.")

            # Start the async batch job
            job = self.app.async_batch_scrape_urls(
                urls,
                {
                    "formats": ["json"],
                    "jsonOptions": {
                        "schema": ExtractSchema.model_json_schema(),
                    },
                },
            )

            job_id = job.get("id")
            if not job_id:
                logging.error("Failed to start async batch job.")
                return []

            logging.info(f"Async batch scrape started. Job ID: {job_id}")

            # Polling for job completion (max 10 attempts)
            for attempt in range(10):
                time.sleep(10)  # Wait x seconds before checking status
                status = self.app.check_batch_scrape_status(job_id)

                if status.get("status") == "completed":
                    logging.info("Batch scrape completed successfully.")

                    # Extract article data from each batch item + attach hash
                    articles = []
                    for item in status.get("data", []):
                        if "json" in item:
                            article_data = item["json"]
                            url = article_data.get("link")
                            article_data["hash"] = links_w_hashes[url]
                            articles.append(article_data)

                    return articles

                logging.info(
                    f"Batch scrape status: {status.get('status')} (Attempt {attempt + 1}/10)"
                )

            logging.error("Async batch scrape timed out before completion.")
            return []

        except RequestException as re:
            logging.error(f"Network error during async batch scraping: {re}")
        except Exception as e:
            logging.error(f"Unexpected error in function: {e}")

        return []

    def run(self):
        """
        1) Scrapes all feeds for article links.
        2) Extracts article content in batches.
        """
        articles = []
        links_w_hashes = {}  # new links with associated hashes

        for feed in self.feeds:
            logging.info(f"Scraping links from feed: {feed}")

            # Scrape all links from the feed
            links = self.get_links(feed)
            if not links:
                logging.info(f"No links found for {feed}")
                continue

            # Filter out non-article links
            filtered_links = self.filter_links(links, feed)

            # Check for duplicates using a hash of the URL
            TEST = filtered_links[:2]
            for url in TEST:
                hash = self.generate_hash(url)
                if self.check_hash(hash):
                    logging.info(f"Skipping duplicate: {url}")
                else:
                    links_w_hashes[url] = hash

            if links_w_hashes:
                logging.info(f"Batch scraping {len(TEST)} articles from {feed}")
                if len(TEST) < 10:
                    batch_articles = self.batch_scrape(links_w_hashes)
                else:
                    batch_articles = self.batch_scrape_async(links_w_hashes)
                articles.extend(batch_articles)

        return articles
