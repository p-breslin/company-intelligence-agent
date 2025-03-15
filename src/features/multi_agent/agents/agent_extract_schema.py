import json
import logging
from features.multi_agent.LLM import call_llm

from ..config import Configuration
from ..base_agent import BaseAgent
from ..events import Event, EventType
from ..prompts import EXTRACTION_PROMPT


class ExtractionAgent(BaseAgent):
    """
    1.  Listens for RESEARCH_COMPILED. When triggered:
    2.  Finalizes the JSON extraction.
    3.  Publishes EXTRACTION_COMPLETE.
    """

    def __init__(self, name: str, event_queue, state, completion_queue):
        super().__init__(name, event_queue, state)
        self.completion_queue = completion_queue

    async def handle_event(self, event: Event) -> None:
        """
        Overrides handle_event from BaseAgent.
        """
        if event.type == EventType.RESEARCH_COMPILED:
            logging.info(f"[{self.name}] Received {event.type.value} event.")
            await self.extract_schema()

    async def extract_schema(self) -> None:
        logging.info(f"[{self.name}] Extracting final schema.")
        cfg = Configuration()

        if not self.state.research:
            logging.warning(
                f"[{self.name}] No research notes available for extraction."
            )
            return

        instructions = EXTRACTION_PROMPT.format(
            schema=self.state.output_schema, research=self.state.research
        )

        output = call_llm(
            cfg.OPENAI_API_KEY,
            messages=[{"role": "user", "content": instructions}],
            schema=self.state.output_schema,
        )
        try:
            data = json.loads(output)
            self.state.final_output = data
            self.state.complete = True
            logging.info(f"[{self.name}] Final output successfully parsed as JSON.")
        except json.JSONDecodeError:
            logging.error(f"[{self.name}] Failed to parse JSON from LLM response.")
            logging.error(f"[{self.name}] LLM response was: {output}")
            self.state.final_output = {}

        logging.info(f"[{self.name}] Publishing EXTRACTION_COMPLETE event.")
        await self.completion_queue.put("EXTRACTION_COMPLETE")
