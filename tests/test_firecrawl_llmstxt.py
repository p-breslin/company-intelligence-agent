import os
import json
import logging
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FireCrawlLLMs:
    def __init__(self):
        try:
            load_dotenv()
            self.app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
            logging.info("Firecrawl initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize Firecrawl: {e}")
            raise

    def run(self, feed, filename="firecrawl_llms_test"):
        # Define generation parameters
        params = {
            "maxUrls": 2,  # Maximum URLs to analyze
            "showFullText": True,  # Include full text in results
        }

        # Generate LLMs.txt with polling
        results = self.app.generate_llms_text(url=feed, params=params)

        # Access generation results
        if results["success"]:
            print(f"Status: {results['status']}")
            print(f"Generated Data: {results['data']}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")

        with open(f"data/{filename}.json", "w", encoding="utf-8") as f:
            json.dump(results["data"], f, indent=4)


def view_data(filename="firecrawl_llms"):
    with open(f"data/{filename}.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
        print(articles)


def test():
    filename = "fc_extract_test"

    feed = "https://www.lightreading.com"
    llmtxt = FireCrawlLLMs()
    llmtxt.run(feed, filename=filename)

    view_data(filename)


# test()


def post_test():
    import requests

    url = "https://api.firecrawl.dev/v1/llmstxt"

    payload = {
        "url": "https://www.lightreading.com",
        "maxUrls": 2,
        "showFullText": True,
    }
    api = os.getenv("FIRECRAWL_API_KEY")
    headers = {"Authorization": f"Bearer {api}", "Content-Type": "application/json"}

    response = requests.request("POST", url, json=payload, headers=headers)

    print(response.text)


# post_test()
