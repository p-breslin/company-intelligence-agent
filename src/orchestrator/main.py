"""
FastAPI Backend for Company Intelligence Agent
----------------------------------------------
This backend provides a search API that:
1. Receives a query and a category from a request.
2. Extracts relevant documents from a Vector Database using a similarity search.
3. Feeds query+content into local LLM using a pre-defined prompt.
4. Returns LLM-generated response, as well as addtional metadata.

Key Features:
- FastAPI
- Vector Database (choice of ChromaDB or Weaviate) for document retrieval
- CORS for frontend communication
- Local LLM for refining response
"""

import logging
from fastapi import FastAPI, Query
from app.main.local_LLM import LocalLLM
from fastapi.middleware.cors import CORSMiddleware
from app.main.embedding_search import EmbeddingSearch

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)


class CIA:
    def __init__(self):
        self.LLM = LocalLLM()
        self.cache = {}
        self.database = "weaviate"

    def engine(self, query: str, category: str = None, session_id: str = None):
        """Handles queries, info retrieval, LLM refinement, follow-ups."""

        # Identify if new session or following up a previous session
        follow_up = session_id in self.cache

        # Directly do a similarity search if not a follow-up query
        if not follow_up:
            logging.info("Retrieving RAG data...")
            vector_search = EmbeddingSearch(query, database=self.database)
            retrieved_data, LLM_context = vector_search.run()

            # Generate refined response using Local LLM (single-turn)
            logging.info("Generating response...")
            llm_response = self.LLM.generate_response(query, LLM_context)

            # Store chat history AND* the full article (*once per session)
            if session_id:
                if session_id not in self.cache:
                    self.cache[session_id] = {
                        "conversation": self.LLM.conversation_history,
                        "full_article": retrieved_data["content"],
                    }
                else:
                    self.cache[session_id]["conversation"] = (
                        self.LLM.conversation_history
                    )

        else:
            logging.info(f"Follow-up query: {query}, Session ID: {session_id}")

            self.LLM.conversation_history = self.cache[session_id]["conversation"]

            # Retrieve full article from cache if available
            logging.info("Retrieving full-article content from cache")
            retrieved_text = self.cache[session_id].get("full_article", "")

            # Generate response using conversation history (multi-turn)
            logging.info("Generating the follow-up response...")
            llm_response = self.LLM.generate_response(
                query,
                retrieved_text=retrieved_text,
                prompt="follow_up",
                multi_turn=True,
            )

            # Update conversation history
            logging.info("Updating the conversation history")
            self.cache[session_id]["conversation"] = self.LLM.conversation_history

        return {
            "query": query,
            "category": category,
            "results": retrieved_data if not follow_up else [],
            "llm_response": llm_response,
            "session_id": session_id,
        }


# FastAPI initialization
app = FastAPI()
agent = CIA()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (maybe restrict later)
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/engine")
async def engine(
    q: str = Query(..., description="Search query"),
    category: str = None,
    session_id: str = None,
):
    """
    Handles GET requests to the /engine endpoint.
    - @app.get("/engine") is a FastAPI decorator
    - This registers engine() as a handler for HTTP GET requests to the endpoint
    - q is a required (...) query parameter that must be a string
    """
    return agent.engine(q, category, session_id)
