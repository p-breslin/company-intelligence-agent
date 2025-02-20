import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from utils.scraping_utils import *
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser


class AsyncScraper:
    def __init__(self, incomplete):
        """
        Performs web scraping asynchronously for increased efficiency.
        Initialize with the list of URLs (incomplete RSS feed data) to scrape.
        """
        self.incomplete = incomplete

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
            logging.error(f"Error fetching robots.txt from {source}: {e}")
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
            logging.warning("You are not respecting robots.txt...")
        await asyncio.sleep(delay)  # Respect crawl delay

        try:
            # Asynchronous context management
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    logging.error(
                        f"Failed to fetch {url} - Status Code: {response.status}"
                    )
                    return url, None

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Extract missing info using functions from utils.scraping_utils
                if not article["title"]:
                    article["title"] = extract_title(soup)
                if not article["published"]:
                    article["published"] = extract_published_date(soup)
                if not article["summary"]:
                    article["summary"] = extract_summary(soup)
                if not article["content"]:
                    article["content"] = extract_content(soup)
                if not article["tags"]:
                    article["tags"] = extract_tags(soup)

                # Temporary workaround: if no content, use the summary
                if not article["content"]:
                    article["content"] = article["summary"]

                return url, article

        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return url, None

    async def scrape_articles(self, articles):
        """Asyncchronous scraping for multiple articles (all at once)."""
        if not self.incomplete:
            logging.info("No articles need scraping.")
            return []

        logging.info(f"Scraping {len(self.incomplete)} articles asynchronously...")

        tasks = []
        # Create a session object to be reused for multiple HTTP requests
        async with aiohttp.ClientSession() as session:
            for url in self.incomplete:
                # Find the relevant article that needs scraping
                article = next((a for a in articles if a["link"] == url), None)
                if article:
                    tasks.append(self.single_scrape(session, url, article))

            # Concurrently run multiple asynchronous tasks in parallel
            scraped_results = await asyncio.gather(*tasks)
        return scraped_results

    def async_scrape(self, articles):
        """Starts async scraping and updates missing content."""
        scraped_data = asyncio.run(self.scrape_articles(articles))

        # Merge scraped data back into list of articles
        for url, data in scraped_data:
            if data:
                for article in articles:
                    if article["link"] == url:
                        article.update(data)
                        break

        logging.info("Async scraping complete.")
