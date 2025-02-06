import time
import psycopg
import requests
from dateutil import parser
from bs4 import BeautifulSoup
from operator import itemgetter
from utils.config import config
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from utils.helpers import compute_hash, clean_raw_html


class WebScraper:
    def __init__(self, targets):
        self.targets = targets
        self.db = config.get_section("DB_USER")
        self.schema = config.get_section("schema")


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


    def scrape(self):
        """Scrapes web page only for a few attributes."""
        articles = []
        headers = {"User-Agent": "Mozilla/5.0"} # spoofs browser to avoid bot detection

        for url in self.targets:
            source = urlparse(url).netloc # Removing https:// for consistency

            # Get permission and crawl delay in one call
            permission, delay = self.respect_robots(source)
            if not permission:
                print(f"Skipping {url} as per robots.txt")
                continue

            time.sleep(delay)  # Respect the delay before scraping

            try:
                # Retrieve HTML content of the page
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error fetching {url}: {e}")
                return None

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Initialize with None values for all database fields (efficient?)
            data = {db_field: None for db_field in self.schema.keys()}
            data['link'] = url
            data['source'] = source

            # Loop through database fields and look for desired items
            for db_field in self.schema.keys():

                if db_field == "title":
                    value = soup.find(db_field).text.strip() if soup.find(db_field) else None
                    data[db_field] = value

                # Published date: search for <meta> tag with property
                if db_field == "published":
                    date = soup.find('meta', {'property': 'article:published_time'})
                    if date and "content" in date.attrs:
                        published = date['content']
                        if published:
                            try:
                                published = parser.parse(published)
                                data[db_field] = published
                            except Exception as e:
                                print(f"Error parsing date '{published}': {e}")

                if db_field == "content":
                    raw = soup.find('article').text.strip() if soup.find('article') else None
                    if raw:
                        value = clean_raw_html(raw, feed='web') # Clean article text
                        data[db_field] = value

                if db_field == "summary":
                    # Search for summary using description or OpenGraph attributes
                    for x in [{"name": "description"}, {"property": "og:description"}]:
                        tag = soup.find("meta", x)
                        if tag and "content" in tag.attrs:
                            data[db_field] = tag['content']
                            break  # Stop if a valid summary is found

                if db_field == "tags":
                    tags = soup.find("meta", {"name": "keywords"})
                    if tags and "content" in tags.attrs:
                        data[db_field] = tags['content']

                if db_field == "hash":
                    # Compute hash for deduplication
                    hash = compute_hash(data['title'], data['source'])
                    data[db_field] = hash

            articles.append(data)
            
        self.store_scraped_data(articles)


    def store_scraped_data(self, articles):
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
        print("Web scraped data successfully stored in PostgreSQL table.")


if __name__ == "__main__":
    targets = config.get_list("test_sites")
    scraper = WebScraper(targets)
    scraper.scrape()