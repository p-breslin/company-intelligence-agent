import re
import json
import asyncio
import aiohttp
import hashlib
import logging
from google import genai
from mistralai import Mistral
from crawl4ai import AsyncWebCrawler
from utils.config import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

"""Scraper using Crawl4AI with Jina.ai and an LLM API."""


class ScraperAI:
    def __init__(self, feeds, db_conn, LLM="mistral"):
        try:
            self.feeds = feeds
            self.cur = db_conn.cursor()  # For postgreSQL set-up

            # Pre-defined LLM prompt
            config = ConfigLoader("llmConfig")
            self.prompt = config.get_value("data_extraction_prompt")
            self.model = config.get_section("models")[LLM]

            # API keys
            config = ConfigLoader("API_KEYS")
            self.jina_key = config.get_value("jina")  # Jina.ai reader
            llm_key = config.get_value(LLM)  # LLM API key

            if not llm_key:
                raise ValueError("LLM API key missing. Please check config.")
            if not self.jina_key:
                raise ValueError("Jina API key missing. Please check config.")

            # LLM client set-up
            if LLM == "gemini":
                self.client = genai.Client(api_key=llm_key)
            if LLM == "mistral":
                self.client = Mistral(api_key=llm_key)

            # Semaphore to enforce rate limits (RPM)
            self.LLM_semaphore = asyncio.Semaphore(30)
            self.Jina_semaphore = asyncio.Semaphore(10)

            # Retry logic (will use an exponential backoff for the delay)
            self.retries = 5
            self.retry_delay = 1

        except Exception as e:
            logging.error(f"Failed to initialize: {e}")
            raise

    def generate_hash(self, link):
        """Generates an MD5 hash for a given link (webpage URL)."""
        return hashlib.md5(link.encode("utf-8")).hexdigest() if link else None

    def check_hashes(self, hashes):
        """Batch checks if hashes exists in the PostgreSQL database."""
        placeholders = ", ".join(["%s"] * len(hashes))
        query = f"SELECT hash FROM articles WHERE hash IN ({placeholders})"
        self.cur.execute(query, tuple(hashes))
        return {row[0] for row in self.cur.fetchall()}

    def clean_LLM_response(self, response):
        """Cleans LLM response to remove weird unwanted formatting."""
        return re.sub(r"^```json\s*|\s*```$", "", response.strip()).strip()

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
            async with self.Jina_semaphore:  # Rate limits
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
                        self.retry_delay = 1  # Reset delay on success
                        return url, await response.text()

                except Exception as e:
                    logging.error(f"Failed to fetch Markdown for {url}: {e}")
                    await asyncio.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff

        logging.error(f"Markdown fetch failed after {self.retries} retries: {url}")
        return url, None

    async def scrape_single_article(self, session, url, hash):
        """Scrapes a single article asynchronously using LLM API."""
        url, markdown = await self.fetch_markdown(session, url)
        if not markdown:
            return None

        for attempt in range(self.retries):  # Retry logic
            async with self.LLM_semaphore:  # Rate limits
                try:
                    if attempt > 0:
                        logging.info(f"Attempt {attempt + 1})")

                    if self.model == "gemini":
                        # asyncio.to_thread for asynchronous call
                        query = self.prompt + markdown
                        response = await asyncio.to_thread(
                            self.client.models.generate_content,
                            model=self.model,
                            contents=query,
                        )
                        cleaned = self.clean_LLM_response(response.text)

                    elif self.model == "mistral":
                        # complete_async for asynchronous call
                        query = [
                            {"role": "system", "content": f"{self.prompt}"},
                            {"role": "user", "content": f"{markdown}"},
                        ]
                        response = await self.client.chat.complete_async(
                            model=self.model, messages=query, timeout=15
                        )
                        cleaned = self.clean_LLM_response(
                            response.choices[0].message.content
                        )

                    try:
                        # Parse JSON response
                        article_data = json.loads(cleaned)
                        article_data.update({"link": url, "hash": hash})
                        return article_data
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to parse JSON ({url}): {e}")
                        return None

                # Retry logic
                except Exception as e:
                    error_message = str(e)

                    # Rate limits reached (429)
                    if "RESOURCE_EXHAUSTED" in error_message or "429" in error_message:
                        logging.warning("LLM rate limit hit. Retrying..")
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

    async def process_articles(self, links_w_hashes):
        """Processes all articles asynchronously."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.scrape_single_article(session, url, hash)
                for url, hash in links_w_hashes.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if not isinstance(r, Exception)]

    async def run_scraping(self):
        """
        1) Scrapes all feeds for article links.
        2) Converts link to markdown using Jina.ai reader.
        3) Extracts article content using LLM API call.
        """
        articles = []
        links_w_hashes = {}

        for feed in self.feeds:
            # Scrape links from the feed asynchronously
            logging.info(f"Scraping links from feed: {feed}")
            links = await self.get_links(feed)
            if not links:
                logging.info(f"No links found for {feed}")
                continue

            # Filter out non-article links
            filtered = self.filter_links(links)

            # Check for duplicates (batch calling the hash function)
            hashes = {url: self.generate_hash(url) for url in filtered[:1]}
            existing_hashes = self.check_hashes(hashes.values())  # returns set
            if existing_hashes:
                logging.info(f"Skipping {len(existing_hashes)} duplicates")
            links_w_hashes = {
                url: hash for url, hash in hashes.items() if hash not in existing_hashes
            }

            # Process articles asynchronously
            if links_w_hashes:
                logging.info(f"Async processing {len(links_w_hashes)} articles")
                batch_articles = await self.process_articles(links_w_hashes)
                articles.extend(batch_articles)

        return articles
