import os
import time
import json
import logging
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ExtractSchema(BaseModel):
    link: str = Field(description="The URL of the article.")
    title: str = Field(description="Title of the article")
    published: str = Field(description="The published date of the article")
    tags: list[str] = Field(description="Three keywords related to the article")
    content: str = Field(description="The full article text")


class FirecrawlExtractor:
    def __init__(self, links):
        load_dotenv()
        self.links = links
        self.app = FirecrawlApp(os.getenv("FIRECRAWL_API"))

    def batch_extract(self):
        """Uses Firecrawl's batch extraction to scrape list of URL links."""
        try:
            # Define the extraction parameters
            extract_params = {
                "prompt": "Extract the URL link, title, published date, tags, and full content from the page.",
                "schema": ExtractSchema.model_json_schema(),
            }

            # Firecrawl's async_extract submits batch jobs
            job = self.app.async_batch_scrape_urls(
                self.links, {"formats": ["extract"], "extract": extract_params}
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
                    print(status["data"])
                    logging.info("Batch extraction completed.")
                    return status["data"]

                logging.info(f"Batch job in progress: {status['completed']} completed")

            logging.warning("Batch job timed out before completion.")
            return []

        except Exception as e:
            logging.error(f"Error during batch extraction: {e}")
            return []


if __name__ == "__main__":
    links = [
        "https://www.musicmagpie.co.uk/blog/2024/03/15/what-is-the-most-popular-apple-product-right-now/",
        "https://thewatchesgeek.com/best-apple-products/",
    ]

    extractor = FirecrawlExtractor(links=links)
    data = extractor.batch_extract()
    with open("test_extract.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
