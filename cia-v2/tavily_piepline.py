import os
import asyncio
import logging
from dotenv import load_dotenv
from pydantic import BaseModel
from utils.config import ConfigLoader
from arango_pipeline import GraphDBHandler
from backend.LLM_integration import LocalLLM
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
        self.N = 3  # how many links to scrape
        self.links = []
        self.llm = LocalLLM()
        self.config = ConfigLoader("config")
        self.tavily_tool = TavilySearchResults(
            api_key=os.getenv("TAVILY_API"),
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )

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

        # Add URL links for scraping
        for res in results[0][: self.N]:
            self.links.append(res["url"])
        return results["answer"]

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
        for res in results[0][: self.N]:
            self.links.append(res["url"])
        return results["answer"]

    async def run_search(self, company):
        """Runs both searches in parallel using asyncio.gather()."""
        products, competitors = await asyncio.gather(
            self.get_products(company), self.get_competitors(company)
        )
        return {"products": products, "competitors": competitors}

    def send_to_firecrawl(self):
        """Send links to Firecrawl to be scraped."""


async def main(company):
    engine = TavilySearch()
    products, competitors = await asyncio.gather(
        engine.get_products(company), engine.get_competitors(company)
    )
