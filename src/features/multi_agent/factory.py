import logging
import asyncio
from typing import List

from .base_agent import BaseAgent
from .state import OverallState
from .agents.agent_check_database import DatabaseAgent
from .agents.agent_generate_queries import QueryGenerationAgent
from .agents.agent_web_search import WebSearchAgent
from .agents.agent_compile_research import ResearchAgent
from .agents.agent_extract_schema import ExtractionAgent

"""
Centralizes creation of agent instances. Each specialized agent is imported and instantiated, then returns them as a list. The coordinator then starts them.
"""


def create_agents(
    event_queue: asyncio.Queue, completion_queue: asyncio.Queue, state: OverallState
) -> List[BaseAgent]:
    """
    Instantiates and configures all agent classes, injecting the shared
    event queue and shared state.
    """

    agents: List[BaseAgent] = [
        DatabaseAgent(name="DatabaseAgent", event_queue=event_queue, state=state),
        QueryGenerationAgent(
            name="QueryGenerationAgent", event_queue=event_queue, state=state
        ),
        WebSearchAgent(name="WebSearchAgent", event_queue=event_queue, state=state),
        ResearchAgent(name="ResearchAgent", event_queue=event_queue, state=state),
        ExtractionAgent(
            name="ExtractionAgent",
            event_queue=event_queue,
            state=state,
            completion_queue=completion_queue,
        ),
    ]
    return agents
