from utils.config import config
from rss_handler import RSSHandler
from async_scraper import AsyncScraper
from utils.helpers import store_to_postgres


if __name__ == "__main__":
    feeds = ["https://www.fierceelectronics.com/rss/xml"]
    # feeds = config.get_list("rss_feeds")
    rss_handler = RSSHandler(feeds)
    articles = rss_handler.fetch()  # Fetch RSS data

    if rss_handler.incomplete:  # Scrape if there is incomplete data
        scraper = AsyncScraper(rss_handler.incomplete)
        scraper.async_scrape(articles) 

    store_to_postgres(articles)  # Save to database