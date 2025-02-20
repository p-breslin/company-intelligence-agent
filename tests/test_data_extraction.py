import feedparser
import pandas as pd
from utils.config import config
from backend.rss_handler import RSSHandler
from backend.web_scraper import Webcraper


class TestDataExtraction:
    def __init__(self):
        self.feeds = [
            "https://www.nasa.gov/news-release/feed/",
        ]
        self.raw_rss = []
        self.test_rss = None
        self.test_scraper = None

    def raw_rss_feed(self):
        for url in self.feeds:
            feed = feedparser.parse(url)

            for entry in feed.entries:
                data = {field: None for field in config.get_section("schema").keys()}

                for field in data.keys():
                    value = getattr(entry, field, None)
                    data[field] = value

                self.raw_rss.append(data)

    def rss_handler(self):
        rss = RSSHandler(self.feeds)
        self.test_rss = rss.fetch()

    def save_tables(self, comp1, comp2, name1, name2, savename):
        # Converts raw and cleaned test data into DataFrames
        A = pd.DataFrame(comp1)
        B = pd.DataFrame(comp2)
        A.insert(0, "Type", f"name1")
        B.insert(0, "Type", f"name2")
        stacked = pd.concat([A, B]).sort_index(kind="stable").reset_index(drop=True)
        stacked.to_csv(f"data/{savename}.csv", index=False)

    def run(self):
        self.raw_rss_feed()
        self.rss_handler()
        self.save_tables(
            comp1=self.raw_rss,
            comp2=self.test_rss,
            name1="Raw RSS",
            name2="Clean RSS",
            savename="test_RSS",
        )

        # Going to fake a pass to the web scraper
        self.test_scraper = [
            {field: None for field in config.get_section("schema").keys()}
            for _ in self.test_rss
        ]

        # Labelling every entry as incomplete (do this by flagging each URL)
        incomplete = [entry["link"] for entry in self.test_rss]

        # Add URL values from self.raw to test list
        for entry, new_entry in zip(self.test_rss, self.test_scraper):
            new_entry["link"] = entry["link"]

        scraper = Webcraper(incomplete)
        scraper.async_scrape(self.test_scraper)

        self.save_tables(
            comp1=self.test_rss,
            comp2=self.test_scraper,
            name1="Clean RSS",
            name2="Web Scraper",
            savename="test_scraper",
        )


if __name__ == "__main__":

    test = TestDataExtraction()
    test.run()
