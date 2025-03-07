import os
import asyncio
import logging
from dotenv import load_dotenv
from pydantic import BaseModel
from tavily import AsyncTavilyClient
from utils.config import ConfigLoader
from backend.LLM_integration import LocalLLM
from firecrawl_extract import FirecrawlScraper


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
        logging.info("Product search complete.")

        # Add URL links for scraping (response is a list of dictionaries)
        prod_links = [res["url"] for res in response["results"][: self.N]]
        self.links.extend(prod_links)
        return response["answer"]  # LLM summary of results

    async def get_competitors(self, company):
        """Web searches the biggest competitors for the given company."""
        query = self.config["prompt_competitors"].format(company=company)
        response = await self.client.search(query, **self.search_params)
        logging.info("Competitors search complete.")

        # Add URL links for scraping (response is a list of dictionaries)
        comp_links = [res["url"] for res in response["results"][: self.N]]
        self.links.extend(comp_links)
        return response["answer"]  # LLM summary of results

    async def run_firecrawl(self):
        """Schedules FirecrawlScraper.run() in a separate thread."""
        if not self.links:
            logging.warning("No links to scrape.")
            return

        # Ensure we don’t create a new event loop unnecessarily
        loop = asyncio.get_running_loop()
        logging.info(
            f"Starting Firecrawl for {len(self.links)} links in a background thread..."
        )

        # Offload the blocking function to a thread to unblock the main loop
        self.firecrawl_task = loop.run_in_executor(
            None,  # uses default ThreadPoolExecutor
            self.extract.run,  # the blocking function
            self.links,  # argument
        )

    async def run_search(self, company):
        """
        1. Get products & competitors in parallel.
        2. Start Firecrawl extraction in the background.
        3. Return results immediately so UI can display them without waiting.
        """
        products, competitors = await asyncio.gather(
            self.get_products(company), self.get_competitors(company)
        )

        # Start Firecrawl AFTER all links are collected
        if self.links:
            await (
                self.run_firecrawl()
            )  # we 'await' so the method can set up the task & return quickly

        return {"products": products, "competitors": competitors, "links": self.links}


async def search_engine(company):
    engine = TavilySearch()
    results = await engine.run_search(company)

    # Return engine so we can wait for Firecrawl later
    return results, engine.firecrawl_task
