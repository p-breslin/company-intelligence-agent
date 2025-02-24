import re
import json
import asyncio
import aiohttp
import hashlib
import logging
from google import genai
from crawl4ai import AsyncWebCrawler
from utils.config import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

"""Scraper using Crawl4AI with Jina.ai and Gemini API."""


class CJGscraper:
    def __init__(self, feeds, db_conn):
        try:
            self.feeds = feeds
            self.cur = db_conn.cursor()  # For postgreSQL set-up

            # Pre-defined LLM prompt
            config = ConfigLoader("testsConfig")
            self.prompt = config.get_value("data_extraction_prompt")

            # Jina and Gemini API keys
            config = ConfigLoader("API_KEYS")
            gemini_key = config.get_value("gemini")
            self.jina_key = config.get_value("jina")

            if not gemini_key:
                raise ValueError("Gemini API key missing. Please check config.")
            if not self.jina_key:
                raise ValueError("Jina API key missing. Please check config.")

            # API set-up
            self.client = genai.Client(api_key=gemini_key)
            self.model = "gemini-2.0-flash-lite-preview-02-05"

            # Semaphore to enforce rate limits (Gemini: 30 RPM, Jina: 200 RPM)
            self.gemini_semaphore = asyncio.Semaphore(30)
            self.markdown_semaphore = asyncio.Semaphore(10)

            # Retry logic (will use an exponential backoff for the delay)
            self.retries = 5
            self.retry_delay = 1

        except Exception as e:
            logging.error(f"Failed to initialize: {e}")
            raise

    def generate_hash(self, link):
        """Generates an MD5 hash for a given link (webpage URL)."""
        return hashlib.md5(link.encode("utf-8")).hexdigest() if link else None

    def check_hash(self, hash):
        """Checks if the hash already exists in the PostgreSQL database."""
        self.cur.execute("SELECT 1 FROM articles WHERE hash = %s LIMIT 1", (hash,))
        return self.cur.fetchone() is not None

    def clean_gemini_response(self, response_text):
        """Cleans Gemini response to remove weird unwanted formatting."""
        # Remove triple backticks and optional "json" label (```json ```)
        text = re.sub(r"^```json\s*|\s*```$", "", response_text.strip())
        return text.strip()

    async def get_links(self, homepage):
        """Crawl the homepage and extract article URLs using Crawl4AI."""
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=homepage)

                # Extract only relevant links
                if result.success:
                    article_links = [
                        link["href"]
                        for link in result.links.get("internal", [])
                        if link["href"].startswith(homepage)
                    ]
                    return article_links
                else:
                    print("Failed to crawl homepage")
                    return []

        except Exception as e:
            logging.error(f"Unexpected error in function: {e}")
        return []

    def filter_links(self, links, min_word_count=4):
        """Determines if link is likely an article based on its last segment."""
        filtered = []
        for link in links:
            end = link.rstrip("/").split("/")[-1]  # last segment of the URL
            words = re.split(r"[-_]", end)  # split on hyphens / underscores

            # Count words (allowing words with numbers)
            word_count = sum(1 for w in words if re.match(r"^[a-zA-Z0-9]+$", w))

            # Must have at least min_word_count
            if word_count >= min_word_count:
                filtered.append(link)

        return filtered

    async def fetch_markdown(self, session, url):
        """Fetches Markdown asynchronously using Jina.ai (with rate limits)"""

        api_url = f"https://r.jina.ai/{url}"
        headers = {"Authorization": f"Bearer {self.jina_key}"}

        # Make calls asynchronously
        for attempt in range(self.retries):  # Retry logic
            async with self.markdown_semaphore:  # Rate limits
                try:
                    # POST request passes options; GET request fetches data only
                    async with session.get(
                        api_url, headers=headers, timeout=15
                    ) as response:
                        if response.status == 429:  # Too many requests
                            logging.warning("Jina rate limit hit. Retrying..")
                            await asyncio.sleep(self.retry_delay)
                            self.retry_delay *= 2  # Exponential backoff
                            continue

                        response.raise_for_status()  # for non-200 responses
                        return url, await response.text()

                except Exception as e:
                    logging.error(f"Failed to fetch Markdown for {url}: {e}")

                    await asyncio.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff

        logging.error(f"Markdown fetch failed after {self.retries} retries: {url}")
        return url, None

    async def scrape_single_article(self, session, url, article_hash):
        """Scrapes a single article asynchronously using Gemini API."""
        try:
            # Fetch Markdown asynchronously
            url, markdown = await self.fetch_markdown(session, url)
            if not markdown:
                return None

            # Combine with pre-defined prompt
            query = self.prompt.format(WEBPAGE_MARKDOWN=markdown)

            for attempt in range(self.retries):  # Retry logic
                async with self.gemini_semaphore:  # Rate limits
                    try:
                        logging.info(f"Processing (attempt {attempt + 1}): {url}")
                        response = await asyncio.to_thread(
                            self.client.models.generate_content,
                            model=self.model,
                            contents=query,
                        )

                        # Extract and clean the response text
                        gemini_output = response.text
                        cleaned = self.clean_gemini_response(gemini_output)

                        try:
                            # Parse JSON response
                            article_data = json.loads(cleaned)
                            article_data["link"] = url  # Attach link
                            article_data["hash"] = article_hash  # Attach hash
                            return article_data
                        except json.JSONDecodeError as e:
                            logging.error(f"Failed to parse JSON ({url}): {e}")
                            return None

                    # Retry logic
                    except Exception as e:
                        error_message = str(e)

                        # Rate limits reached (429)
                        if (
                            "RESOURCE_EXHAUSTED" in error_message
                            or "429" in error_message
                        ):
                            logging.warning("Gemini rate limit hit. Retrying..")
                            await asyncio.sleep(self.retry_delay)
                            self.retry_delay *= 2  # Exponential backoff

                        # Temporary issues (503, timeouts)
                        elif "503" in error_message or "timeout" in error_message:
                            logging.warning(f"Temporary issue. Retrying..")
                            await asyncio.sleep(self.retry_delay)
                            self.retry_delay *= 2

                        else:
                            # Stop retrying if it's a permanent failure
                            logging.error(f"Permanent error (not retried): {e}")
                            return None

            logging.error(f"Failed after {self.retries} retries: {url}")
            return None

        except Exception as e:
            logging.error(f"Error in function: {e}")
            return None

    async def process_articles(self, links_w_hashes):
        """Processes all articles asynchronously."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.scrape_single_article(session, url, article_hash)
                for url, article_hash in links_w_hashes.items()
            ]
            return await asyncio.gather(*tasks)

    async def run_scraping(self):
        """
        1) Scrapes all feeds for article links.
        2) Extracts article content asynchronously.
        """
        articles = []
        links_w_hashes = {}

        for feed in self.feeds:
            logging.info(f"Scraping links from feed: {feed}")

            # Scrape links from the feed asynchronously
            links = await self.get_links(feed)
            if not links:
                logging.info(f"No links found for {feed}")
                continue

            # Filter out non-article links
            filtered_links = self.filter_links(links)

            # Check for duplicates
            for url in filtered_links[:1]:
                hash = self.generate_hash(url)
                if self.check_hash(hash):
                    logging.info(f"Skipping duplicate: {url}")
                else:
                    links_w_hashes[url] = hash

            # Process articles asynchronously
            if links_w_hashes:
                logging.info(
                    f"Processing {len(links_w_hashes)} articles asynchronously"
                )
                batch_articles = await self.process_articles(links_w_hashes)
                articles.extend(batch_articles)

        return articles
