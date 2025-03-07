import os
import json
import time
import logging
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from utils.config import ConfigLoader
from utils.helpers import generate_hash

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ExtractSchema(BaseModel):
    link: str = Field(description="The URL of the article.")
    title: str = Field(description="Title of the article")
    published: str = Field(description="The published date of the article")
    tags: list[str] = Field(description="Three keywords related to the article")
    content: str = Field(description="The full article text")


class FirecrawlScraper:
    def __init__(self):
        load_dotenv()
        self.app = FirecrawlApp(os.getenv("FIRECRAWL_API"))
        self.config = ConfigLoader("config")

    def async_batch_scrape(self, links):
        """Uses Firecrawl's batch extraction to scrape list of URL links."""
        try:
            # Define the extraction parameters
            extract_params = {
                "prompt": self.config.get_value("firecrawl_extract"),
                "schema": ExtractSchema.model_json_schema(),
                "onlyMainContent": True,
                "ignoreInvalidURLs": True,
            }

            # Firecrawl's async_extract submits batch jobs
            job = self.app.async_batch_scrape_urls(
                links, {"formats": ["extract"], "extract": extract_params}
            )

            if not job["id"]:
                raise ValueError("Failed to start batch job.")
            logging.info(f"Batch job started. Job ID: {job['id']}")

            # Poll for job completion
            for _ in range(120):
                time.sleep(10)

                status = self.app.check_batch_scrape_status(job["id"])
                if not status["success"]:
                    logging.error(
                        f"Failed to retrieve batch job status for {job['id']}"
                    )
                    break

                if status["status"] == "completed":
                    logging.info("Batch extraction completed.")
                    return status["data"]

                logging.info(f"Batch job in progress: {status['completed']} completed")

            logging.warning("Batch job timed out before completion.")
            return []

        except Exception as e:
            logging.error(f"Error during batch extraction: {e}")
            return []

    def run(self, links):
        articles = self.async_batch_scrape(links)
        if articles:
            for article in articles:
                article["extract"]["hash"] = generate_hash(article["extract"]["link"])

        # with open("test_extract.json", "w", encoding="utf-8") as f:
        #     json.dump(articles, f, indent=4, ensure_ascii=False)

        return articles
