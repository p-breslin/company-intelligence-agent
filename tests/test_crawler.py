import asyncio
import logging
from utils.config import config
from app.data_extraction.smart_extraction.crawler import CrawlLinks

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def test_crawler_multiple(feeds):
    """
    Runs the crawler on multiple feed URLs concurrently and prints results.
    """
    crawler = CrawlLinks()

    async def process_feed(feed):
        """Helper function to crawl a single feed and return results."""
        try:
            articles = await crawler.run(feed)
            return (feed, articles)
        except Exception as e:
            logging.error(f"Error crawling {feed}: {e}")
            return (feed, None)

    # Run all feeds concurrently
    tasks = [process_feed(feed) for feed in feeds]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for feed, articles in results:
        if isinstance(articles, Exception) or articles is None:
            print(f"\nFailed to crawl: {feed}")
        elif not articles:
            print(f"\nNo articles found for: {feed}")
        else:
            print(f"\nArticles extracted from {feed}:")
            for article in articles:
                print(f"- {article}")


if __name__ == "__main__":
    feeds = config.get_list("feeds")
    asyncio.run(test_crawler_multiple(feeds))
