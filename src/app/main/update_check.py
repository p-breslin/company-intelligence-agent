import logging
import psycopg
from utils.config import config
from firecrawl import FirecrawlApp
from utils.helpers import check_hash, import_postgres_data

if __name__ == "__main__":
    """
    Unified pipeline for data extraction, storage, and embedding.
    Collects and runs Scraper, SQL storage, and Embedding routines.
    """

    # Connect to PostgreSQL
    db_user = config.get_section("DB_USER")
    try:
        conn = psycopg.connect(**db_user)
    except Exception as e:
        logging.error("Database connection failed:", e)
        raise

    conn.autocommit = True
    articles = import_postgres_data(
        db_conn=conn,
        data=config.get_section("weaviate")["fields"],
        only_new=False,
    )

    # Hash is set as the second value; URL link is third... this is a bit dodge
    link_w_hash = {}
    for article in articles:
        link_w_hash[article[2]] = article[1]
    conn.close()

    # We should hash the URL with the update date and check that --> firecrawl?
    app = FirecrawlApp(api_key="fc-445ee151fdf2488091d114f5a4f801ea")
    test_url = "https://www.fierceelectronics.com/iot-wireless/less-more-sequans-targets-eredcap-5g-iot-mwc"

    # Scrape parameters
    params = {
        "formats": ["markdown"],
        "onlyMainContent": True,
        "includeTags": [
            "meta[property='article:published_time']",
            "meta[name='publishedTime']",
            "meta[name='parsely-pub-date']",
            "meta[property='article:modified_time']",
            "meta[name='lastModified']",
        ],
        "excludeTags": ["script", ".ad", "#footer", "p", "div", "span", "img", "a"],
        "waitFor": 1000,
    }

    # Perform the scrape request
    response = app.scrape_url(url=test_url, params=params)
    # print(response)

    # Extract metadata from the response
    allowed_keys = {
        "article:published_time",
        "publishedTime",
        "parsely-pub-date",
        "article:modified_time",
        "lastModified",
    }
    metadata = response.get("metadata", {})
    filtered_metadata = {
        key: value for key, value in metadata.items() if key in allowed_keys
    }

    date_published = metadata.get("datePublished")
    date_modified = metadata.get("dateModified")

    # Determine the most recent date
    date_published = (
        filtered_metadata.get("article:published_time")
        or filtered_metadata.get("publishedTime")
        or filtered_metadata.get("parsely-pub-date")
    )
    date_modified = filtered_metadata.get(
        "article:modified_time"
    ) or filtered_metadata.get("lastModified")
    most_recent_date = (
        max(date_published, date_modified)
        if date_published and date_modified
        else date_published or date_modified
    )

    # Output the most recent date
    print(
        "Most Recent Date:", most_recent_date if most_recent_date else "No date found"
    )
