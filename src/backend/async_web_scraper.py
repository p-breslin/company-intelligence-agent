import asyncio
import aiohttp
from dateutil import parser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from utils.helpers import compute_hash, clean_html


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
            # Asynchronous context management
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
        print("Async scraping complete.")