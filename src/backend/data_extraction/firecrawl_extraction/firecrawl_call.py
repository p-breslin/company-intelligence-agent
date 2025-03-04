import time
import logging
from firecrawl import FirecrawlApp
from utils.config import ConfigLoader
from pydantic import BaseModel, Field
from utils.helpers import generate_hash


class ArticleSchema(BaseModel):
    # link: str = Field(description="The URL of the article.")
    # title: str = Field(description="Title of the article")
    # published: str = Field(description="The published date of the article")
    # tags: list[str] = Field(description="Three keywords related to the article")
    # content: str = Field(description="The full article text")
    link: str
    title: str
    published: str
    keywords: list[str]
    content: str


class ArticleSchemaResponse(BaseModel):
    # Must wrap the schema in a container class to get multiple articles.
    articles: list[ArticleSchema]


class FireCrawlScraper:
    def __init__(self, feeds):
        try:
            self.feeds = feeds
            self.articles = None
            config = ConfigLoader("API_KEYS")
            api_key = config.get_value("firecrawl")
            if not api_key:
                raise ValueError("API key is missing. Please check config.")
            self.app = FirecrawlApp(api_key=api_key)
            logging.info("Firecrawl initialized.")
        except Exception as e:
            logging.error(f"Failed to initialize Firecrawl: {e}")
            raise

    def attach_hash(self):
        """Hash check will occur when storing to postgres."""
        for article in self.articles:
            hash_value = generate_hash(article["link"])
            article["hash"] = hash_value

    def run(self, batch_job=False):
        # Append an asterisk to each URL to search through the full website
        feeds = [url + "/*" for url in self.feeds]
        logging.info("Feeds prepared for extraction.")

        # Import the Firecrawl prompt
        config = ConfigLoader("config")
        prompt = config.get_value("firecrawl_prompt")

        if batch_job:
            logging.info("Starting batch extraction job...")

            try:
                self.articles = self.app.async_extract(
                    feeds,
                    {
                        "prompt": f"{prompt}",
                        "schema": ArticleSchemaResponse.model_json_schema(),
                        "enableWebSearch": True,
                    },
                )
                logging.info(f"Batch job started with job ID: {self.articles.job_id}")

            except Exception as e:
                logging.error(f"Failed to start batch job: {e}")
                return None

            job_status = self.app.get_extract_status(self.articles.job_id)
            while job_status["status"] != "completed":
                logging.info(f"Progress: {job_status['progress']}")
                time.sleep(10)
                job_status = self.app.get_extract_status(self.articles.job_id)

            logging.info("Batch job completed successfully.")
            self.attach_hash()
            logging.info("Hashes attached to extracted articles.")
            return self.articles[0]["articles"]

        else:
            test_feeds = [feeds[0]]
            logging.info(f"Single feed extraction from: {test_feeds}")

            try:
                # Call the Firecrawl extract method
                self.articles = self.app.extract(
                    test_feeds,
                    {
                        "prompt": f"{prompt}",
                        "schema": ArticleSchemaResponse.model_json_schema(),
                    },
                )
            except Exception as e:
                logging.error(f"Extraction failed: {e}")
                return None

            logging.info("Extraction job completed.")
            print(self.articles)

            # Won't be a list if just one feed
            if not isinstance(self.articles, list):
                self.articles = [self.articles]

            self.attach_hash()
            logging.info("Hashes attached to extracted articles.")
            return self.articles[0]["articles"]
