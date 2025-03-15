import logging
import asyncio

from .events import Event, EventType
from .state import OverallState
from .factory import create_agents


class Orchestrator:
    """
    Orchestrates everything:
    1.  Creates event queue, shared OverallState, agents, and starts them all.
    2.  Publishes a START_RESEARCH event.
    3.  Waits for EXTRACTION_COMPLETE.
    """

    def __init__(self, company: str):
        self.company = company
        self.state = OverallState(company=company)
        self.event_queue = asyncio.Queue()
        self.agents = create_agents(self.event_queue, self.state)

    async def start_system(self):
        """
        Starts all agents and coordinates the system until EXTRACTION_COMPLETE event is receieved.
        """
        logging.info("Orchestrator starting system...")

        # Start each agent in its own task
        tasks = [asyncio.create_task(agent.start()) for agent in self.agents]

        # Initiate the pipeline
        await self.event_queue.put(Event(EventType.START_RESEARCH))

        # Monitor for extraction complete
        while True:
            event = await self.event_queue.get()

            if event.type == EventType.EXTRACTION_COMPLETE:
                logging.info("Extraction complete. Shutting down agents...")
                for _ in self.agents:
                    await self.event_queue.put(Event(EventType.SHUTDOWN))
                break

        # Wait for all agents to finish
        await asyncio.gather(*tasks)

        # At this point, final_output should be populated
        return self.state.final_output


async def run_research_pipeline(company: str):
    """
    A helper function that sets up the Orchestrator, runs the system, and returns final state.
    """
    orchestrator = Orchestrator(company=company)
    final_output = await orchestrator.start_system()
    return final_output


if __name__ == "__main__":
    # For local testing:
    # python orchestrator.py
    company_to_research = "Tesla"
    result = asyncio.run(run_research_pipeline(company_to_research))
    print("Final result:", result)
