import logging
import asyncio

from .events import Event, EventType
from .state import OverallState
from .factory import create_agents

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


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

        # Agents will use this queue for inter-agent event passing
        self.event_queue = asyncio.Queue()

        # Agents can place a "done" message here for the coordinator
        self.completion_queue = asyncio.Queue()

        # Pass both queues to the agent factory
        self.agents = create_agents(
            event_queue=self.event_queue,
            completion_queue=self.completion_queue,
            state=self.state,
        )

    async def start_system(self):
        """
        Starts all agents and coordinates the system until EXTRACTION_COMPLETE event is receieved.
        """
        logging.info("Orchestrator starting system...")

        # Start each agent in its own task
        tasks = [asyncio.create_task(agent.start()) for agent in self.agents]

        # Initiate the pipeline
        await self.event_queue.put(Event(EventType.START_RESEARCH))

        # Wait for the final agent to signal completion in the completion_queue
        done_signal = await self.completion_queue.get()
        if done_signal == "EXTRACTION_COMPLETE":
            logging.info("Extraction complete. Shutting down agents...")
            for _ in self.agents:
                await self.event_queue.put(Event(EventType.SHUTDOWN))

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
