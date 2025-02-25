import re
import json
import asyncio
import aiohttp
import logging
from google import genai
from mistralai import Mistral
from crawl4ai import AsyncWebCrawler
from utils.config import ConfigLoader
from utils.helpers import generate_hash, check_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

"""Scraper using Crawl4AI with Jina.ai and an LLM API."""


class RateLimiter:
    """Time-based rate limiter to handle API request."""

    def __init__(self, max_rpm: int):
        self.interval = 60.0 / max_rpm  # seconds between calls
        self.last_call = 0.0
        self.lock = asyncio.Lock()  # ensures only one task updates last_call

    async def wait_for_slot(self):
        """Wait until enough time has passed since the last request."""
        async with self.lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_call  # seconds since last call
            wait_time = self.interval - elapsed

            # Sleep if wait needed
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # Record a fresh call time
            self.last_call = asyncio.get_event_loop().time()


class ScraperAI:
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

            # Rate limiters (RPM)
            self.jina_limiter = RateLimiter(10)
            self.llm_limiter = RateLimiter(30)

        except Exception as e:
            logging.error(f"Failed to initialize: {e}")
            raise

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
                    logging.warning(f"Failed to crawl homepage: {homepage}")
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

        # We'll do up to self.retries attempts with exponential backoff
        retry_delay = 1  # Reset retry delay before each url
        for attempt in range(1, self.retries + 1):
            await self.jina_limiter.wait_for_slot()  # Wait for rate slot

            try:
                # POST request passes options; GET request fetches data only
                async with session.get(api_url, headers=headers) as response:
                    # Retry logic
                    if response.status == 429:  # Too many requests
                        logging.warning("Jina rate limit hit. Retrying..")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue

                    response.raise_for_status()  # for non-200 responses
                    markdown = await response.text()
                    return url, markdown

            # Retry fallback
            except Exception as e:
                logging.error(f"Failed to fetch Markdown for {url}: {e}")
                if attempt < self.retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2

        # If all retries exhausted
        logging.error(f"Markdown fetch failed after retries for: {url}")
        return url, None

    async def scrape_link(self, session, url, hash):
        """
        Scrapes a single link asynchronously:
            1) Fetches markdown using Jina reader.
            2) Calls LLM to extract structured info from the markdown.
        """
        url, markdown = await self.fetch_markdown(session, url)
        if not markdown:
            return None

        # Attempt LLM calls with exponential backoff
        retry_delay = 1
        for attempt in range(1, self.retries + 1):
            await self.llm_limiter.wait_for_slot()
            logging.info(f"LLM call: attempt {attempt}")

            # Construct query and pass to LLM
            try:
                if self.LLM == "gemini":
                    query = self.prompt + markdown
                    # No native async call for Gemini so must run in a thread
                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model=self.model,
                        contents=query,
                        config={"response_mime_type": "application/json"},
                    )
                    json_response = response.text

                elif self.LLM == "mistral":
                    query = [
                        {"role": "system", "content": f"{self.prompt}"},
                        {"role": "user", "content": f"{markdown}"},
                    ]
                    # Native method for Mistral's async call
                    response = await self.client.chat.complete_async(
                        model=self.model,
                        messages=query,
                        response_format={"type": "json_object"},
                    )
                    json_response = response.choices[0].message.content

                # Attempt to parse the JSON response
                try:
                    article = json.loads(json_response)
                    # Add url link and hash (and check for published errors)
                    article.update({"link": url, "hash": hash})
                    article["published"] = article.get("published", "unknown")
                    return article
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse JSON for ({url}): {e}")
                    return None

            except Exception as e:
                error_message = str(e)

                # Rate limits or temporary issues (503, timeouts)
                if "RESOURCE_EXHAUSTED" in error_message or "429" in error_message:
                    logging.warning("LLM rate limit hit (429). Retrying..")
                elif "503" in error_message or "timeout" in error_message:
                    logging.warning("503/timeout issue. Retrying..")
                else:
                    logging.error(f"Non-retriable failure: {e}")
                    return None

                if attempt < self.retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2

        logging.error(f"Failed LLM call after after retries for: {url}")
        return None

    async def process_scraping(self, session, links_w_hashes):
        """Processes scrapes for all links asynchronously."""
        tasks = [
            self.scrape_link(session, url, hash) for url, hash in links_w_hashes.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r for r in results if not isinstance(r, Exception)
        ]  # filters out exceptions

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

        # Check for duplicates by generating and checking hashes
        hashes = {url: generate_hash(url) for url in filtered[:1]}
        stored_hashes = check_hash(self.cur, hashes.values())  # returns a set
        if stored_hashes:
            logging.info(f"Skipping {len(stored_hashes)} duplicates for {feed}")

        # Filter out duplicates if necessary
        links_w_hashes = {
            url: hash for url, hash in hashes.items() if hash not in stored_hashes
        }
        if not links_w_hashes:
            logging.info(f"No new articles to process for {feed}")
            return []

        # Process articles
        logging.info(f"Processing {len(links_w_hashes)} articles from {feed}")
        articles = await self.process_scraping(session, links_w_hashes)
        logging.info(f"Finished processing articles for {feed}")
        return articles

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

        # Flatten all results (and skip any exceptions)
        articles = []
        for result in results_per_feed:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                logging.error(f"Error in processing feed: {result}")

        return articles
