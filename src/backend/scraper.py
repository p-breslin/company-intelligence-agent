import time
import requests
from dateutil import parser
from bs4 import BeautifulSoup
from utils.config import config
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
from utils.helpers import compute_hash, clean_raw_html

import sys


class WebScraper:
    def __init__(self, rss_data, incomplete):
        self.rss_data = rss_data
        self.incomplete = incomplete
        self.db = config.get_section("DB_USER")
        self.schema = config.get_section("schema")


    def respect_robots(self, source):
        """
        Determines if scraping is allowed and what the crawl delay is.
        If no delay, still rate limit to avoid getting blocked.
        """
        
        robots_url = urljoin(source, "/robots.txt")
        rp = RobotFileParser()
        
        try:
            rp.set_url(robots_url)
            rp.read()
            allowed = rp.can_fetch("*", source)  # Check permission
            delay = rp.crawl_delay("*") or 2  # Default delay if not specified
            return allowed, delay
        except Exception as e:
            print(f"Error fetching robots.txt from {source}: {e}")
            return True, 2  # Assume scraping is allowed with default delay


    def scrape(self):
        """Scrapes web page for missing attributes."""
        # Info we fail to scrape will get unknown str (can't give ChromaDB None types)
        unknown = "unknown"
        headers = {"User-Agent": "Mozilla/5.0"} # spoofs browser (bot detection)

        for id, feed in zip(self.incomplete, self.rss_data):
            # Only scrape the ids given by the list of incomplete dictionaries
            if not id:
                continue
            # Get permission and crawl delay in one call
            permission, delay = self.respect_robots(feed["link"])
            if not permission:
                print(f"Skipping {feed["link"]} as per robots.txt")
                continue
            time.sleep(delay)  # Respect the delay before scraping

            try:
                # Retrieve HTML content of the page
                response = requests.get(feed["link"], headers=headers, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error fetching {feed["link"]}: {e}")
                return None

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            for article in self.rss_data:

                # Loop through database fields and look for desired items if missing
                for field, entry in article.items():

                    if entry is not None:
                        continue

                    if field == "title":
                        value = soup.find(field).text.strip() if soup.find(field) else unknown
                        feed[field] = value

                    # Published date: search for <meta> tag with property
                    if field == "published":
                        feed[field] = unknown # default
                        date = soup.find('meta', {'property': 'article:published_time'})
                        if date and "content" in date.attrs:
                            published = date['content']
                            if published:
                                try:
                                    published = parser.parse(published)
                                    feed[field] = published
                                except Exception as e:
                                    print(f"Error parsing date '{published}': {e}")

                    if field == "summary":
                        # Search for summary using description or OpenGraph attributes
                        for x in [{"name": "description"}, {"property": "og:description"}]:
                            tag = soup.find("meta", x)
                            if tag and "content" in tag.attrs:
                                feed[field] = tag['content']
                                break  # Stop if a valid summary is found
                            else:
                                feed["summary"] = unknown

                    if field == "content":
                        raw = soup.find('article').text.strip() if soup.find('article') else None
                        if raw:
                            value = clean_raw_html(raw, feed='web') # Clean article text
                            feed[field] = value
                        else:
                            # Set content as summary if no content found
                            feed[field] = feed["summary"]
                            feed.pop("summary") # only keep content

                    if field == "tags":
                        tags = soup.find("meta", {"name": "keywords"})
                        if tags and "content" in tags.attrs:
                            feed[field] = tags['content']
                        else:
                            # TO-DO: ML CLASSIFIER
                            feed[field] = unknown                    

                    if field == "hash":
                        # Compute hash for deduplication
                        hash = compute_hash(feed['title'], feed['source'])
                        feed[field] = hash

        return self.rss_data