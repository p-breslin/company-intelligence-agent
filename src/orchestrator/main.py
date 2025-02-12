"""
FastAPI Backend for Company Intelligence Agent
----------------------------------------------
This backend provides a search API that:
1. Receives a query and a category from a request.
2. Extracts relevant documents from ChromaDB using a similarity search.
3. Feeds query+content into local LLM using a pre-defined prompt.
4. Returns LLM-generated response, as well as addtional metadata.

Key Features:
- FastAPI
- ChromaDB for document retrieval
- CORS for frontend communication
- Local LLM for refining response
"""

import chromadb
import urllib.parse
from utils.config import config
from fastapi import FastAPI, Query
from backend.LLM_integration import LocalLLM
from fastapi.middleware.cors import CORSMiddleware


class CIA:
    def __init__(self):
        self.LLM = LocalLLM()
        self.cache = {}

        # Initialize ChromaDB client and collection
        try:
            chroma = config.get_section("chroma")
            client = chromadb.PersistentClient(path=chroma["root"])
            self.collection = client.get_or_create_collection(name=chroma["dbname"])
            print("ChromaDB initialized successfully.")
        except Exception as e:
            print(f"ChromaDB Initialization Failed: {e}")
            self.collection = None

    def engine(self, query: str, category: str = None, session_id: str = None):
        """Handles queries, info retrieval, LLM refinement, follow-ups."""

        # Identify if new session or following up a previous session
        follow_up = session_id in self.cache

        if not follow_up:
            # Similarity search on ChromaDB embeddings WITH category filtering
            try:
                print(f"Query: '{query}', Category: '{category}'")

                if category == "Any":
                    results = self.collection.query(
                        query_texts=[query],
                        n_results=1,
                        include=["documents", "metadatas"],
                    )
                else:
                    # Category filtering by looking at Metadata
                    # SKIPPING due to inability
                    filter = {"tags": {"$in": [category]}}

                    if filter:
                        results = self.collection.query(
                            query_texts=[query],
                            n_results=1,
                            include=["documents", "metadatas"],
                            # where=filter,
                        )
            except Exception as e:
                print(f"Error querying ChromaDB: {e}")
                return {"error": "Failed to retrieve search results"}

            # Extract relevant content from retrieved information
            docs = results.get("documents", [])
            metadatas = results.get("metadatas", [])

            # Ensure we have retrieved content
            if not docs:
                return {
                    "query": query,
                    "category": category,
                    "results": [],
                    "llm_response": "No relevant data found.",
                }

            # Formatting retrieved information for the output
            retrieved_information = [
                {
                    # Ensure article is a string
                    "article": " ".join(doc) if isinstance(doc, list) else doc,
                    "title": metadata.get("title", "Unknown Title"),
                    "published": metadata.get("published", "Unknown Date"),
                    "source": metadata.get("source", "Unknown Source"),
                    "tags": metadata.get("tags", "No Tags").split(","),
                }
                # results["documents"]: list of strings
                for doc, metadata_list in zip(docs, metadatas)
                # results["metadatas"]: list of lists; each list has metadata dict
                for metadata in (
                    metadata_list
                    if isinstance(metadata_list, list) and metadata_list
                    else [{}]
                )
            ]

            # Combine  texts for LLM input (flatten doc lists into one str)
            retrieved_text = "\n".join(
                doc if isinstance(doc, str) else " ".join(doc) for doc in docs
            )
            print("Generating response...")
            # Generate refined response using Local LLM (single-turn)
            llm_response = self.LLM.generate_response(query, retrieved_text)

            # Store chat history AND* the full article (*once per session)
            if session_id:
                if session_id not in self.cache:
                    self.cache[session_id] = {
                        "conversation": self.LLM.conversation_history,
                        "full_article": "\n".join(
                            (
                                urllib.parse.unquote(doc)
                                if isinstance(doc, str)
                                else " ".join(doc)
                            )
                            for doc in docs
                        ),
                    }
                else:
                    self.cache[session_id][
                        "conversation"
                    ] = self.LLM.conversation_history

        else:
            print("Using conversation history for your follow-up question.")
            print(f"Follow-up query: {query}, Session ID: {session_id}")

            self.LLM.conversation_history = self.cache[session_id]["conversation"]

            # Retrieve full article from cache if available
            full_article = self.cache[session_id].get("full_article", "")
            retrieved_text = full_article  # Use full article for follow-ups

            print(
                f"Using full article for follow-up in session {session_id}: {full_article[:500]}..."
            )

            # Generate response using conversation history (multi-turn)
            llm_response = self.LLM.generate_response(
                query,
                retrieved_text=retrieved_text,
                prompt="follow_up",
                multi_turn=True,
            )

            # Update conversation history
            self.cache[session_id]["conversation"] = self.LLM.conversation_history

        return {
            "query": query,
            "category": category,
            "results": retrieved_information if not follow_up else [],
            "llm_response": llm_response,
            "session_id": session_id,
        }


# FastAPI initialization
app = FastAPI()
agent = CIA()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for now, restrict later)
    allow_credentials=True,
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

    > @app.get("/engine") is a FastAPI decorator that registers engine() as a handler for HTTP GET requests to the endpoint.
    > q is a required (...) query parameter that must be a string.
    > description="Search query" adds documentation.
    """
    return agent.engine(q, category, session_id)
