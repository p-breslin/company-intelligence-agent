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
    # Semaphores (for rate limits) are class-level to share among all instances
    LLM_semaphore = asyncio.Semaphore(3)
    Jina_semaphore = asyncio.Semaphore(3)

    def __init__(self, feeds, db_conn, LLM="mistral"):
        try:
            self.LLM = LLM
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

    async def crawl_links(self, homepage):
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
            logging.error(f"Unexpected error crawling links: {e}")
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
        async with self.Jina_semaphore:  # Rate limits
            for attempt in range(self.retries):  # Retry logic
                self.retry_delay = 1  # Reset rery delay before each attempt
                try:
                    # POST request passes options; GET request fetches data only
                    async with session.get(api_url, headers=headers) as response:
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

    async def scrape_link(self, session, url, hash):
        """
        Scrapes a single link asynchronously using LLM API.
            1) Fetches markdown.
            2) Uses LLM to extract structured info from the markdown.
        """
        url, markdown = await self.fetch_markdown(session, url)
        if not markdown:
            return None

        async with self.LLM_semaphore:  # Rate limits
            logging.info(f"Started LLM processing...")

            for attempt in range(self.retries):  # Retry logic
                # self.retry_delay = 1  # Reset rery delay before each attempt
                try:
                    logging.info(f"LLM attempt {attempt + 1}")
                    if self.LLM == "gemini":
                        # asyncio.to_thread required for gemini async call
                        query = self.prompt + markdown
                        response = await asyncio.to_thread(
                            self.client.models.generate_content,
                            model=self.model,
                            contents=query,
                            config={"response_mime_type": "application/json"},
                        )
                        json_response = response.text

                    elif self.LLM == "mistral":
                        # Native complete_async for Mistral's async call
                        query = [
                            {"role": "system", "content": f"{self.prompt}"},
                            {"role": "user", "content": f"{markdown}"},
                        ]
                        response = await self.client.chat.complete_async(
                            model=self.model,
                            messages=query,
                            response_format={"type": "json_object"},
                        )
                        json_response = response.choices[0].message.content

                    try:
                        # Parse JSON response
                        article_data = json.loads(json_response)
                        article_data.update({"link": url, "hash": hash})
                        return article_data
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to parse JSON ({url}): {e}")
                        return None

                except Exception as e:
                    error_message = str(e)

                    # Rate limits
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
                        # Stop retrying if it's a total failure
                        logging.error(f"Failure: {e}")
                        return None
        self.retry_delay = 1
        logging.error(f"Failed LLM call after {self.retries} retries: {url}")
        return None

    async def process_scraping(self, session, links_w_hashes):
        """Processes scrapes for all links asynchronously."""
        tasks = [
            self.scrape_link(session, url, hash) for url, hash in links_w_hashes.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logging.info("Finished processing articles for feed.")
        return [r for r in results if not isinstance(r, Exception)]

    async def process_feed(self, feed, session):
        """
        Process a single feed:
        1) Crawl homepage for links
        2) Filter out non-article links
        3) Check database for duplicates
        4) Scrape links via Jina markdown and LLM call
        """
        logging.info(f"Scraping links from feed: {feed}")
        links = await self.crawl_links(feed)

        if not links:
            logging.info(f"No links found for {feed}")
            return []
        logging.info(f"Found {len(links)} links for {feed}")

        # Filter out non-article links
        filtered = self.filter_links(links)
        logging.info(f"Filtered down to {len(filtered)} links for {feed}")

        # Check for duplicates (batch calling the hash function)
        hashes = {url: self.generate_hash(url) for url in filtered[:20]}
        existing_hashes = self.check_hashes(hashes.values())  # returns set
        if existing_hashes:
            logging.info(f"Skipping {len(existing_hashes)} duplicates for {feed}")
        links_w_hashes = {
            url: h for url, h in hashes.items() if h not in existing_hashes
        }

        # Process articles asynchronously if any remain
        if links_w_hashes:
            logging.info(f"Processing {len(links_w_hashes)} articles")
            articles = await self.process_scraping(session, links_w_hashes)
            logging.info(f"Finished processing articles for {feed}")
            return articles

        logging.info(f"No new articles to process for {feed}")
        return []

    async def run(self):
        """
        1) For each feed, fetch and process article links in parallel.
        2) Use a single aiohttp.ClientSession for all calls.
        3) Return all scraped articles across feeds.
        """
        async with aiohttp.ClientSession() as session:
            # Gather tasks for each feed in parallel
            tasks = [self.process_feed(feed, session) for feed in self.feeds]
            results_per_feed = await asyncio.gather(*tasks, return_exceptions=True)

        # Debug: Check if any tasks are still running
        pending = [t for t in asyncio.all_tasks() if not t.done()]
        if pending:
            logging.warning(f"Found {len(pending)} pending tasks: {pending}")
            for task in pending:
                logging.warning(f"Pending Task Details: {task}")

        # Flatten the lists (and skip any exceptions)
        articles = []
        for result in results_per_feed:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                logging.error(f"Error in processing feed: {result}")

        return articles
