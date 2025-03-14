import re
import json
import logging

from ..config import Configuration
from ..base_agent import BaseAgent
from ..events import Event, EventType
from ..prompts import QUERY_LIST_PROMPT, QUERY_GENERATOR_PROMPT

from features.multi_agent.LLM import call_llm


class QueryGenerationAgent(BaseAgent):
    """
    Listens for NEED_QUERIES. When triggered, it generates queries via the LLM and stores them in state.search_queries. Then it emits QUERIES_GENERATED.
    """

    async def handle_event(self, event: Event) -> None:
        """
        Overrides handle_event from BaseAgent.
        """
        if event.type == EventType.NEED_QUERIES:
            logging.info(f"[{self.name}] Received NEED_QUERIES event.")
            self.generate_queries()

    def generate_queries(self) -> None:
        """
        Generates search queries using LLM.
        """
        cfg = Configuration()

        instructions = QUERY_GENERATOR_PROMPT.format(
            company=self.state.company,
            schema=json.dumps(self.state.output_schema, indent=2),
            N_searches=cfg.N_searches,
        )
        messages = [
            {"role": "system", "content": instructions},
            {
                "role": "user",
                "content": QUERY_LIST_PROMPT.format(N_searches=cfg.N_searches),
            },
        ]
        output = call_llm(cfg.OPENAI_API_KEY, messages)

        search_queries = re.findall(r'"\s*(.*?)\s*"', output)  # clean if needed
        self.state.search_queries = search_queries
        logging.info(
            f"{self.name} generated search queries: {self.state.search_queries}"
        )

        logging.info(f"{self.name} Publishing QUERIES_GENERATED event.")
        self.publish_event(EventType.QUERIES_GENERATED)
