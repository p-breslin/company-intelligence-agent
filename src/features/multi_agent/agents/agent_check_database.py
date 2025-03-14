import logging
from ..base_agent import BaseAgent
from ..events import Event, EventType
from app.main.embedding_search import EmbeddingSearch


class DatabaseAgent(BaseAgent):
    """
    1.  Checks whether relevant data is already stored in a database.
    2.  If data; stores it in state.search_results and notifies other agents.
    3.  If no data; triggers query generation.
    """

    async def handle_event(self, event: Event) -> None:
        """
        Overrides handle_event from BaseAgent.
        """
        if event.type == EventType.START_RESEARCH:
            logging.info(f"[{self.name}] Received START_RESEARCH event.")
            await self.check_database()

    async def check_database(self) -> None:
        logging.info(f"[{self.name}] Checking the database...")

        vector_search = EmbeddingSearch(self.state.company)
        metadata, docs = vector_search.run()

        if not metadata:
            logging.info(
                f"[{self.name}] No stored data found; publishing NEED_QUERIES event."
            )
            await self.publish_event(EventType.NEED_QUERIES)
        else:
            logging.info(
                f"[{self.name}] Found data in DB; updating state and publishing DB_CHECK_DONE event."
            )
            self.state.search_results = [
                {
                    "url": metadata["link"],
                    "title": metadata["title"],
                    "content": docs,
                    "raw_content": None,
                }
            ]
            logging.info(f"[{self.name}] Publishing DB_CHECK_DONE event.")
            await self.publish_event(EventType.DB_CHECK_DONE)
