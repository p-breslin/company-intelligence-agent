import psycopg
import feedparser
import scraper
from dateutil import parser
from operator import itemgetter
from utils.config import config
from urllib.parse import urlparse
from utils.helpers import compute_hash, clean_raw_html

import sys


class RSSFeedFetcher:
    def __init__(self, feeds):
        """Initialize with the database configuration details."""
        self.db = config.get_section("DB_USER")
        self.schema = config.get_section("schema")
        self.feeds = feeds
        self.articles = []


    def fetch(self):
        """Fetch and parse RSS feed data."""
        incomplete = [[] for _ in range(len(self.feeds))]
        for index, url in enumerate(self.feeds):
            feed = feedparser.parse(url)
            source = getattr(feed.feed, "link", None)

            # Loop through every feed entry and add data to a dict
            for entry in feed.entries:
                data = {}

                # Loop over the desired fields in the feed
                for field in self.schema.keys():
                    if field in {'title', 'link', 'author', 'summary'}:
                        value = getattr(entry, field, None)
                        if value and field=='title':
                            value = clean_raw_html(value, feed='rss')
                        data[field] = value

                    if field == 'published':
                    # Parse and convert RSS date string into Python datetime object
                        value = getattr(entry, field, None)
                        if value:
                            date = entry.published
                            try:
                                date = parser.parse(date)
                            except Exception as e:
                                print(f"Error parsing date '{date}': {e}")
                                date = None
                            data[field] = date

                    if field == 'source':
                        # Removing https:// for consistency
                        data[field] = urlparse(source).netloc

                    if field == 'content':
                    # If there is full content, extract clean text from HTML
                        value = getattr(entry, field, None)
                        if value:
                            raw = entry.content[0].value
                            content = clean_raw_html(raw, feed='rss')
                        else:
                            content = getattr(entry, 'summary', None)
                        data[field] = content

                    if field == 'tags':
                        value = getattr(entry, field, None)
                        if value:
                            value = value[0]['term']
                        data[field] = value
                    
                    if field == 'hash':
                        hash = compute_hash(data['title'], data['source'])
                        data['hash'] = hash

                    if any(value is None for value in data.values()):
                        incomplete[index].append(hash)

                self.articles.append(data)
        print("RSS feed data fetched successfully.")
        
        # Check if any of the inner lists are NOT empty; scrape if so
        if any(value for value in incomplete):
            print("Scraping missing fields when necessary.")
            self.articles = scraper.WebScraper(self.articles, incomplete).scrape()
        self.store(self.articles)
        

    def store(self, articles):
        """
        Inserts RSS articles into PostgreSQL database.
        Prevents duplicate entries using the hash.
        """
        try:
            conn = psycopg.connect(**self.db)
            with conn.cursor() as cur:
                try:
                    # Get column names dynamically from schema
                    columns = list(self.schema.keys())
                    # Create placeholders for values
                    placeholders = ", ".join(["%s"] * len(columns))
                    # Join column names for SQL query
                    col_names = ", ".join(columns) 

                    # Construct dynamic INSERT statement 
                    insert_query = f"""
                        INSERT INTO articles ({col_names})
                        VALUES ({placeholders})
                        ON CONFLICT (hash) DO NOTHING;
                    """

                    # Execute query dynamically
                    getter = itemgetter(*columns) # optimized getter for column order
                    values = [getter(a) for a in articles]
                    cur.executemany(insert_query, values)                    
            
                except Exception as e:
                    print(f"Error inserting article: {e}")
            
            conn.commit()
            conn.close()
            print("RSS data successfully stored in PostgreSQL table.")

        except Exception as e:
            print("Database connection failed:", e)
        

if __name__ == "__main__":
    feeds = config.get_list("rss_feeds")
    # feeds = ["https://www.nasa.gov/news-release/feed/", "https://www.nasa.gov/news-release/feed/"]
    fetcher = RSSFeedFetcher(feeds)
    fetcher.fetch()