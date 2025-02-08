from utils.config import config
from async_rss_handler import RSSHandler
from async_web_scraper import AsyncScraper
from utils.helpers import store_to_postgres


if __name__ == "__main__":
    """Collects and runs RSS and Scraper routines for asynchronous data extraction."""
    # feeds = config.get_list("rss_feeds")
    feeds = ["https://www.fierceelectronics.com/rss/xml"]

    # RSS handler
    rss_handler = RSSHandler(feeds)
    articles = rss_handler.fetch()

    # Activate scraper if there is incomplete data
    if rss_handler.incomplete:
        scraper = AsyncScraper(rss_handler.incomplete)
        scraper.async_scrape(articles) 

    # Save to postgreSQL database
    store_to_postgres(articles)