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
from utils.config import config
from fastapi import FastAPI, Query
from LLM_integration import LocalLLM
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

    def search_engine(self, query: str, category: str = None):
        """Handles the query, retrieves documents, refines with LLM, and caches responses."""

        # Similarity search on ChromaDB embeddings
        try:
            print(f"Query: '{query}', Category: '{category}'")
            results = self.collection.query(
                query_texts=[query], n_results=1, include=["documents", "metadatas"]
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
                "tags": metadata.get("tags", "No Tags Available"),
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

        # Combine retrieved texts for LLM input (flatten doc lists into one str)
        retrieved_text = "\n".join(
            doc if isinstance(doc, str) else " ".join(doc) for doc in docs
        )

        # Generate refined response using Local LLM
        llm_response = self.LLM.generate_response(
            query, retrieved_text, prompt="concise", multi_turn=False
        )

        return {
            "query": query,
            "category": category,
            "results": retrieved_information,
            "llm_response": llm_response,
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


@app.get("/search_engine")
async def search_engine(
    q: str = Query(..., description="Search query"), category: str = None
):
    """
    Handles GET requests to the /search_engine endpoint.

    > @app.get("/search_engine") is a FastAPI decorator that registers search_engine() as a handler for HTTP GET requests to the endpoint.
    > q is a required (...) query parameter that must be a string.
    > description="Search query" adds documentation.
    """
    return agent.search_engine(q, category)
