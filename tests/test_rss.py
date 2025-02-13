import feedparser
import pandas as pd
from dateutil import parser
from utils.config import config
from urllib.parse import urlparse
from utils.helpers import clean_html
from backend.async_rss_handler import RSSHandler


class TestRSSHandler:
    def __init__(self):
        self.feeds = ["https://www.nasa.gov/news-release/feed/"]
        self.raw = []
        self.clean = None

    def raw_rss_feed(self):
        for url in self.feeds:
            feed = feedparser.parse(url)

            for entry in feed.entries:
                data = {field: None for field in config.get_section("schema").keys()}

                for field in data.keys():
                    value = getattr(entry, field, None)
                    data[field] = value

                self.raw.append(data)

    def rss_handler(self):
        rss = RSSHandler(self.feeds)
        self.clean = rss.fetch()


if __name__ == "__main__":
    test = TestRSSHandler()
    test.raw_rss_feed()
    test.rss_handler()

    # Convert raw and clean data into DataFrames
    raw = pd.DataFrame(test.raw)
    clean = pd.DataFrame(test.clean)

    # Stacking them one after the other (for each entry)
    raw["Type"] = "Raw"
    clean["Type"] = "Clean"

    stacked = pd.concat([raw, clean]).sort_index(kind="stable").reset_index(drop=True)

    # with pd.option_context("max_colwidth", 100):
    stacked.to_csv("data/rss_stacked.csv", index=False)

    print(stacked.columns)
