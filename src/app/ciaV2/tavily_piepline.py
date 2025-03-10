import os
import asyncio
import logging
import subprocess
from dotenv import load_dotenv
from tavily import AsyncTavilyClient
from utils.config import ConfigLoader
from app.main.local_LLM import LocalLLM
from app.ciaV2.firecrawl_extract import FirecrawlScraper


class TavilySearch:
    def __init__(self):
        load_dotenv()
        self.N = 1  # how many links to scrape
        self.links = []
        self.llm = LocalLLM()

        # Tavily
        self.cfg = ConfigLoader("config").get_section("tavily")
        self.client = AsyncTavilyClient(os.getenv("TAVILY_API_KEY"))
        self.search_params = {
            "search_depth": "basic",
            "max_results": 2,
            "include_answer": "basic",
            "time_range": "month",
            "topic": "news",
        }

        # Firecrawl
        self.extract = FirecrawlScraper()

    async def get_products(self, company):
        """Web searches the biggest products for the given company."""
        query = self.cfg["prompt_products"].format(company=company)
        response = await self.client.search(query, **self.search_params)
        logging.info("Product search complete.")

        # Add URL links for scraping (response is a list of dictionaries)
        prod_links = [res["url"] for res in response["results"][: self.N]]
        self.links.extend(prod_links)
        return response["answer"]  # LLM summary of results

    async def get_competitors(self, company):
        """Web searches the biggest competitors for the given company."""
        query = self.cfg["prompt_competitors"].format(company=company)
        response = await self.client.search(query, **self.search_params)
        logging.info("Competitors search complete.")

        # Add URL links for scraping (response is a list of dictionaries)
        comp_links = [res["url"] for res in response["results"][: self.N]]
        self.links.extend(comp_links)
        return response["answer"]  # LLM summary of results

    async def run_search(self, company):
        """
        1. Get products & competitors in parallel.
        2. Start Firecrawl extraction in the background.
        3. Return results immediately so UI can display them without waiting.
        """
        products, competitors = await asyncio.gather(
            self.get_products(company), self.get_competitors(company)
        )

        # Start Firecrawl as a background process
        firecrawl_task = subprocess.Popen(
            ["python3", "-m", "firecrawl_extract", *self.links],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logging.info("Firecrawl started in the background.")
        # self.extract.run(self.links)

        return {
            "products": products,
            "competitors": competitors,
            "links": self.links,
        }, firecrawl_task


async def search_engine(company):
    engine = TavilySearch()
    results, firecrawl_task = await engine.run_search(company)
    return results, firecrawl_task
