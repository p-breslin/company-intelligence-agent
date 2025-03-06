import os
import asyncio
import logging
from dotenv import load_dotenv
from pydantic import BaseModel
from utils.config import ConfigLoader
from arango_pipeline import GraphDBHandler
from backend.LLM_integration import LocalLLM
from firecrawl_extract import FirecrawlScraper
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults


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
        self.links = None
        self.llm = LocalLLM()
        self.config = ConfigLoader("config")
        self.tavily_tool = TavilySearchResults(
            api_key=os.getenv("TAVILY_API"),
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )
        self.extract = FirecrawlScraper()
        self.firecrawl_tasks = []  # will run Firecrawl tasks in the background

    async def get_products(self, company):
        """Web searches the biggest products for the given company."""
        query = self.config["tavily"]["products"].format(company)
        results = await self.tavily_tool.abatch(
            [
                {
                    "query": query,
                    "time_range": "year",
                }
            ]
        )

        # Add URL links for scraping and send to firecrawl extractor
        self.links = [res["url"] for res in results[0][: self.N]]

        # Send to Firecrawl extractor
        if self.links:
            logging.info("Sending product links to Firecrawl.")
            task = asyncio.create_task(self.extract.run(self.links))
            self.firecrawl_tasks.append(task)

        return results["answer"] if results else None  # LLM summary of results

    async def get_competitors(self, company):
        """Web searches the biggest competitors for the given company."""
        query = self.config["tavily"]["competitors"].format(company)
        results = await self.tavily_tool.abatch(
            [
                {
                    "query": query,
                    "time_range": "year",
                }
            ]
        )

        # Add URL links for scraping
        self.links = [res["url"] for res in results[0][: self.N]]

        # Send to Firecrawl extractor
        if self.links:
            logging.info("Sending competitor links to Firecrawl.")
            task = asyncio.create_task(self.extract.run(self.links))
            self.firecrawl_tasks.append(task)

        return results["answer"] if results else None  # LLM summary of results

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
        return {"products": products, "competitors": competitors}


async def search_engine(company):
    engine = TavilySearch()
    results = await engine.run_search(company)
    return results, engine  # Return engine so we can wait for Firecrawl later
