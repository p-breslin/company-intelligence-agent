import time
import psycopg
import requests
from dateutil import parser
from bs4 import BeautifulSoup
from utils.config import config
from utils.helpers import compute_hash
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser


class WebScraper:
    def __init__(self, targets):
        self.targets = targets
        self.db = config.get_section("database")


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
        """Scrapes web pages."""
        articles = []
        headers = {"User-Agent": "Mozilla/5.0"} # spoofs browser to avoid bot detection

        for url in self.targets:
            source = urlparse(url).netloc

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

            # Extract title and main content
            soupTitle = soup.find("title")
            title = soupTitle.text.strip() if soupTitle else "No Title"
            soupContent = soup.find("article")
            content = soupContent.text.strip() if soupContent else "Content not found"

            # Extract metadata: search for <meta> tag with property = the published date
            date_meta = soup.find("meta", {"property": "article:published_time"})
            if date_meta and "content" in date_meta.attrs:
                published = date_meta["content"]
                if published:
                    try:
                        published = parser.parse(published)
                    except Exception as e:
                        print(f"Error parsing date '{published}': {e}")
                        published = None

            # Compute hash for deduplication
            hash = compute_hash(title, url)

            articles.append({
                 "title": title,
                 "url": url,
                 "content": content,
                 "published": published,
                 "source": source, # Extract domain as source
                 "hash": hash
                 })
            
        self.store_scraped_data(articles)


    def store_scraped_data(self, articles):
        conn = psycopg.connect(
            dbname = self.db['name'],
            user = self.db['user'],
            password = self.db['pwd'],
            host = self.db['host'],
            port = self.db['port']
        )

        with conn.cursor() as cur:
            try:
                cur.executemany(
                    """
                    INSERT INTO articles (title, link, hash, published, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (hash) DO NOTHING;
                    """,
                    [(a["title"], a["url"], a["hash"], a["published"], a["source"])  for a in articles]
                )
            except Exception as e:
                print(f"Error inserting article: {e}")

        conn.commit()
        conn.close()
        print("Web scraped data successfully stored in PostgreSQL table.")


if __name__ == "__main__":

    targets = [
        "https://www.nasa.gov/news",
        "https://www.investors.com/",
        "https://www.nasa.gov/news",
    ]

    scraper = WebScraper(targets)
    scraper.scrape()