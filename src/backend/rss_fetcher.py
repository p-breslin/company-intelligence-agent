import psycopg
import feedparser
from datetime import datetime

# PostgreSQL connection details
DB_NAME = "database"
DB_USER = "cia"
DB_PASSWORD = "9712d"
DB_HOST = "localhost"
DB_PORT = "5432"

# List of RSS feeds to fetch data from
RSS_FEEDS = [
    "https://www.nasa.gov/rss/dyn/breaking_news.rss"
]

def fetch_rss_data(feed_url):
    """Fetch and parse RSS feed data."""
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.get("summary", ""),  #some feeds may not have a summary
            "published": entry.get("published_parsed", None)
        })
    return articles

def store_in_postgresql(articles):
    """Insert RSS articles into PostgreSQL database."""
    try:
        conn = psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        for article in articles:
            try:
                published_date = (
                    datetime(*article["published"][:6]) if article["published"] else None
                )

                cur.execute("""
                    INSERT INTO rss_articles (title, link, summary, published)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (link) DO NOTHING;
                """, (article["title"], article["link"], article["summary"], published_date))

            except Exception as e:
                print(f"Error inserting article: {e}")

        conn.commit()
        cur.close()
        conn.close()
        print("RSS data successfully stored in PostgreSQL.")

    except Exception as e:
        print("Database connection failed:", e)

def main():
    """Main function to fetch RSS feeds and store them in the database."""
    all_articles = []
    for feed_url in RSS_FEEDS:
        print(f"Fetching data from: {feed_url}")
        articles = fetch_rss_data(feed_url)
        all_articles.extend(articles)
    
    store_in_postgresql(all_articles)

if __name__ == "__main__":
    main()
