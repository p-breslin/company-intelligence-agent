import abc
import logging
import asyncio
from typing import Any
from .state import OverallState
from .events import Event, EventType

"""
========
Summary:
========
 - Defines a template for agents that handle events asynchronously.
 - Processes events from an event queue and acts accordingly.
 - Ensures subclasses implement handle_event; gives specific behavior to agents.
 - Can publish events to the queue for other agents to handle.
"""


class BaseAgent:
    """
    1.	Holds a reference to the shared event queue and shared state.
    2.	Continuously listens for new events (in a loop) and dispatches them.
    3.	Provides a helper to publish new events.

    BaseAgent provides a common structure for all agents in the multi-agent system. Each agent subscribes to an asyncio Queue event bus and processes events as they arrive.
    """

    def __init__(self, name: str, event_queue: asyncio.Queue, state: OverallState):
        self.name = name  # agent's name
        self.event_queue = event_queue
        self.state = state
        self._running = True  # actively running agent flag

    async def start(self) -> None:
        """
        Listens for events.
        """
        logging.info(f"{self.name} started.")

        while self._running:
            try:
                event: Event = await self.event_queue.get()
                logging.debug(f"[{self.name}] Received event: {event}")
                if event.type == EventType.SHUTDOWN:
                    self._running = False
                    continue
                await self.handle_event(event)

            except Exception as e:
                logging.error(f"[{self.name}] Error: {e}")
                await self.publish_event(EventType.ERROR_OCCURRED, {"error": str(e)})

    @abc.abstractmethod
    async def handle_event(self, event: Event) -> None:
        """
        Handles an event based on its type and payload. This is an Abstract Base Class (cannot be instantiated directly): agent classes must subclass BaseAgent and implement how to handle incoming events.
        """
        pass

    async def publish_event(
        self, event_type: EventType, payload: dict[str, Any] = None
    ) -> None:
        """
        Creates and publishes a new event to the queue.
        """
        payload = payload or {}
        event = Event(type=event_type, payload=payload)
        await self.event_queue.put(event)
        logging.info(f"{self.name} published event: {event_type}")

    def __repr__(self):
        return f"<BaseAgent name={self.name}>"
