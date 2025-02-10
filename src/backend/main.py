"""
FastAPI Backend for Company Intelligence Agent
----------------------------------------------
This backend provides a search API that:
1. Receives a query (`q`) and an optional category (`category`) from a request.
2. Searches ChromaDB for relevant documents using the query.
3. Extracts & formats the results before returning them as JSON.

Key Features:
- Uses FastAPI to expose a `/search` endpoint.
- Integrates ChromaDB for document retrieval.
- Enables CORS for frontend communication.

Dependencies:
- FastAPI: Provides the web framework.
- ChromaDB: Manages the document store.
- Config module: Loads database configurations.
"""

import chromadb
from utils.config import config
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for now, restrict later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debugging
print("Initializing ChromaDB Client...")

try:
    # Initialize ChromaDB client and collection
    chroma = config.get_section("chroma")
    client = chromadb.PersistentClient(path=chroma["root"])
    collection = client.get_or_create_collection(name=chroma["dbname"])

except Exception as e:
    print(f"ChromaDB Initialization Failed: {e}")


@app.get("/search")
async def search(q: str = Query(..., description="Search query"), category: str = None):
    """
    Search endpoint to retrieve relevant documents from ChromaDB.

    Parameters:
    - q (str): The search query provided by the user.
    - category (str, optional): The category to refine search results.

    Returns:
    - JSON object with the query, category, and formatted search results.
    """
    print(f"Searching ChromaDB: Query: '{q}', Category: '{category}'")

    # Query ChromaDB for relevant results
    results = collection.query(
        query_texts=[q], n_results=2, include=["documents", "metadatas"]
    )

    # Format results into a structured response
    formatted_results = []
    for idx, (doc, metadata_list) in enumerate(
        zip(results["documents"], results["metadatas"])
    ):
        # Extract metadata safely (handle missing or empty lists)
        metadata = (
            metadata_list[0]
            if isinstance(metadata_list, list) and metadata_list
            else {}
        )

        # Format result entry
        formatted_results.append(
            {
                "id": idx,
                "title": metadata.get("title", "Unknown Title"),
                "summary": doc,
            }
        )
    return {"query": q, "category": category, "results": formatted_results}
