import os
import json
import logging
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FireCrawlExtract:
    def __init__(self):
        try:
            load_dotenv()
            self.app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
            logging.info("Firecrawl initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize Firecrawl: {e}")
            raise

    def run(self, feeds, prompt, schema, filename="firecrawl_extract_test"):
        # Append an asterisk to each URL to search through the full website
        feeds = [url + "/*" for url in feeds]
        logging.info(f"Feed: {feeds[0]}")

        try:
            # Call the Firecrawl extract method
            articles = self.app.extract(
                feeds,
                {
                    "prompt": f"{prompt}",
                    "schema": schema,
                },
            )
        except Exception as e:
            logging.error(f"Extraction failed: {e}")
            return None

        logging.info("Extraction job completed.")
        print(articles)

        with open(f"data/{filename}.json", "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4)


schema = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                    "published_date": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                    "full_content": {"type": "string"},
                },
                "required": [
                    "url",
                    "title",
                    "published_date",
                    "summary",
                    "full_content",
                ],
            },
        }
    },
    "required": ["articles"],
}

prompt = "Extract the latest news articles or blogs. For each article extracted, include the URL, title, published date, three keywords describing the article, a brief summary, and the full unedited article content."


def view_data(filename="firecrawl_extract"):
    with open(f"data/{filename}.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
        print(articles["data"]["articles"][0])


def test():
    filename = "fc_extract_test"

    # feeds = ["https://www.lightreading.com"]
    # scraper = FireCrawlExtract()
    # scraper.run(feeds, prompt, schema, filename=filename)

    view_data(filename)


test()
