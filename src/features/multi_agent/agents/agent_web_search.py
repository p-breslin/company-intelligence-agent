import logging
import asyncio
from tavily import AsyncTavilyClient

from ..base_agent import BaseAgent
from ..config import Configuration
from ..events import Event, EventType
from features.multi_agent.utility import filter_searches


class WebSearchAgent(BaseAgent):
    """
    1.  Listens for QUERIES_GENERATED. When triggered:
    2.  Calls Tavily for each query and stores results in state.search_results.
    3.  Publishes SEARCH_RESULTS_READY.
    """

    async def handle_event(self, event: Event) -> None:
        """
        Overrides handle_event from BaseAgent.
        """
        if event.type == EventType.QUERIES_GENERATED:
            logging.info(f"[{self.name}] Received {event.type.value} event.")
            await self.web_search()

    async def web_search(self) -> None:
        """
        Performs web searches using the Tavily API.
        """
        logging.info(f"[{self.name}] Starting web search with Tavily...")
        cfg = Configuration()
        tavily_async_client = AsyncTavilyClient(cfg.TAVILY_API_KEY)

        if not self.state.search_queries:
            logging.warning(
                f"[{self.name}] No search queries found; cannot perform web search."
            )
            return

        # Asynchronous web searches
        tasks = []
        for query in self.state.search_queries:
            tasks.append(tavily_async_client.search(query, **cfg.TAVILY_SEARCH_PARAMS))
        search_results = await asyncio.gather(*tasks)

        unique_results = filter_searches(search_results)  # filter duplicates
        self.state.search_results = unique_results

        logging.info(f"[{self.name}] Publishing SEARCH_RESULTS_READY event.")
        await self.publish_event(EventType.SEARCH_RESULTS_READY)
