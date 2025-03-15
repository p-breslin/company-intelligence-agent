import logging
from features.multi_agent.LLM import call_llm

from ..config import Configuration
from ..base_agent import BaseAgent
from ..events import Event, EventType
from ..prompts import RESEARCH_PROMPT
from ..utility import format_results


class ResearchAgent(BaseAgent):
    """
    1.  Listens for either DB_CHECK_DONE (if DB had data) or SEARCH_RESULTS_READY (if we had to do a web search).
    2.  Compiles research notes and publishes RESEARCH_COMPILED.
    """

    async def handle_event(self, event: Event) -> None:
        """
        Overrides handle_event from BaseAgent.
        """
        if event.type in [EventType.DB_CHECK_DONE, EventType.SEARCH_RESULTS_READY]:
            logging.info(f"[{self.name}] Received {event.type.value} event.")
            await self.compile_research()

    async def compile_research(self) -> None:
        logging.info(f"[{self.name}] Compiling research notes.")
        cfg = Configuration()

        context_str = format_results(self.state.search_results)
        instructions = RESEARCH_PROMPT.format(
            company=self.state.company,
            schema=self.state.output_schema,
            context=context_str,
        )

        research_notes = call_llm(
            cfg.OPENAI_API_KEY, messages=[{"role": "user", "content": instructions}]
        )
        self.state.research.append(research_notes)
        logging.info(f"[{self.name}] Appended new research notes to state.research.")

        logging.info(f"[{self.name}] Publishing RESEARCH_COMPILED event.")
        await self.publish_event(EventType.RESEARCH_COMPILED)
