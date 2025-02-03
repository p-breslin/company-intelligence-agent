import time
import hashlib
import requests
import feedparser
from bs4 import BeautifulSoup

class ContentCollector:
    def __init__(self, rss_feeds, websites):
        self.rss_feeds = rss_feeds
        self.websites = websites
        self.fetched_articles = set()
        
    def fetch_rss_feeds(self):
        """Fetches articles from RSS feeds while checking for duplicates"""
        articles = []
        for url in self.rss_feeds:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                data = {
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", "Unknown"),
                    "source": url
                }
                if self.is_duplicate(data["link"]): #skip if duplicate
                    continue
                articles.append(data)
                self.mark_as_fetched(data["link"])
        return articles

    def scrape_website(self, url):
        """Attempts to scrape article content from a website"""
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                return None

            # To-Do: generalize to any website
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else "No Title"
            paragraphs = soup.find_all("p")
            content = "\n".join([p.get_text() for p in paragraphs])

            data = {
                "title": title,
                "link": url,
                "content": content[:1000],  #limit preview to save disk space?
                "source": url
            }
            return data
        except requests.RequestException as error:
            print(f"Error scraping {url}: {error}")
            return None

    def is_duplicate(self, url):
        """Checks if the article has been already fetched using a hash"""
        url_hash = hashlib.md5(url.encode()).hexdigest() #converts url into MD5 hash
        return url_hash in self.fetched_articles

    def mark_as_fetched(self, url):
        """Mark an article as fetched"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        self.fetched_articles.add(url_hash)

    def collect_content(self):
        """Fetch content from RSS feeds and scrape specified websites"""
        all_articles = self.fetch_rss_feeds()
        for site in self.websites:
            scraped_article = self.scrape_website(site)
            if scraped_article and not self.is_duplicate(scraped_article["link"]):
                all_articles.append(scraped_article)
                self.mark_as_fetched(scraped_article["link"])
        return all_articles


# Example
if __name__ == "__main__":
    rss_sources = [
        "https://www.experienceflow.ai/feed/"
    ]

    websites_to_scrape = [
        "https://techcrunch.com",
    ]

    collector = ContentCollector(rss_sources, websites_to_scrape)
    
    print("Fetching news articles...")
    collected_articles = collector.collect_content()
    
    for article in collected_articles[:5]:  # Show first 5 articles
        print(f"\nTitle: {article['title']}")
        print(f"Link: {article['link']}")
        print(f"Source: {article['source']}")
        if "content" in article:
            print(f"Content Preview: {article['content'][:200]}...")  # Show preview