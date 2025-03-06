import os
import asyncio
import logging
from dotenv import load_dotenv
from pydantic import BaseModel
from tavily import AsyncTavilyClient
from utils.config import ConfigLoader
from arango_pipeline import GraphDBHandler
from backend.LLM_integration import LocalLLM
from firecrawl_extract import FirecrawlScraper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class CompetitorInfo(BaseModel):
    company: str
    products: list[str]
    strengths: list[str]
    weaknesses: list[str]


class TavilySearch:
    def __init__(self):
        load_dotenv()
        self.N = 1  # how many links to scrape
        self.links = []
        self.llm = LocalLLM()

        # Tavily
        self.config = ConfigLoader("config").get_section("tavily")
        self.client = AsyncTavilyClient(os.getenv("TAVILY_API_KEY"))
        self.search_params = {
            "search_depth": "basic",
            "max_results": 2,
            "include_answer": "basic",
            "time_range": "year",
        }

        # Firecrawl
        self.extract = FirecrawlScraper()
        self.firecrawl_task = None  # will run Firecrawl tasks in the background

    async def get_products(self, company):
        """Web searches the biggest products for the given company."""
        query = self.config["prompt_products"].format(company=company)
        response = await self.client.search(query, **self.search_params)

        # Add URL links for scraping (response is a list of dictionaries)
        prod_links = [res["url"] for res in response["results"][: self.N]]
        self.links.extend(prod_links)
        return response["answer"]  # LLM summary of results

    async def get_competitors(self, company):
        """Web searches the biggest competitors for the given company."""
        query = self.config["prompt_competitors"].format(company=company)
        response = await self.client.search(query, **self.search_params)

        # Add URL links for scraping (response is a list of dictionaries)
        comp_links = [res["url"] for res in response["results"][: self.N]]
        self.links.extend(comp_links)
        return response["answer"]  # LLM summary of results

    async def run_firecrawl(self):
        """Runs Firecrawl extractions in a single batch."""

        if self.links:
            logging.info(f"Starting Firecrawl extraction for {len(self.links)} links.")
            self.firecrawl_task = asyncio.create_task(self.extract.run(self.links))
            await self.firecrawl_task  # Ensure completion
            logging.info("Firecrawl extraction completed.")

    async def wait_for_tasks(self):
        """Waits for Firecrawl extraction to complete."""
        if self.firecrawl_tasks:
            logging.info("Waiting for Firecrawl extraction to finish...")
            await asyncio.gather(*self.firecrawl_tasks)  # Waits for all tasks
            logging.info("Firecrawl extraction is now complete.")

    async def run_search(self, company):
        """Runs both searches in parallel using asyncio.gather()."""
        products, competitors = await asyncio.gather(
            self.get_products(company), self.get_competitors(company)
        )

        # Start Firecrawl AFTER all links are collected
        if self.links:
            self.firecrawl_task = asyncio.create_task(self.run_firecrawl())

        return {"products": products, "competitors": competitors, "links": self.links}


async def search_engine(company):
    engine = TavilySearch()
    results = await engine.run_search(company)

    # Return engine so we can wait for Firecrawl later
    return results, engine.firecrawl_task
