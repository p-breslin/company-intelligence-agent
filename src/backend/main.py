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
from LLM_integration import LocalLLM

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


# Initialize Local LLM processor
LLM = LocalLLM(conversation_limit=5)


@app.get("/search")
async def search(q: str = Query(..., description="Search query"), category: str = None):
    """
    Searches endpoint to retrieve relevant documents from ChromaDB and refines responses with the local LLM.

    Parameters:
    - q (str): The search query provided by the user.
    - category (str, optional): The category to refine search results.

    Returns:
    - JSON object with the query, category, and LLM generated results.
    """
    print(f"Searching ChromaDB: Query: '{q}', Category: '{category}'")

    # Step 1: Query ChromaDB for relevant results
    try:
        results = collection.query(
            query_texts=[q],
            n_results=3,  # Retrieve top 3 most relevant results
            include=["documents", "metadatas"],
        )
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return {"error": "Failed to retrieve search results"}

    # Step 2: Extract relevant content from ChromaDB results
    # Double for-loop flattens nested structure into a simple list of strings
    retrieved_texts = [
        doc for sublist in results.get("documents", []) for doc in sublist
    ]

    # Ensure we have retrieved content, otherwise return an empty response
    if not retrieved_texts:
        return {
            "query": q,
            "category": category,
            "results": [],
            "llm_response": "No relevant data found.",
        }

    # Concatenate retrieved texts for LLM input
    retrieved_content = "\n".join(retrieved_texts)

    # Step 3: Generate refined response using Local LLM
    llm_response = LLM.generate_response(q, retrieved_content, multi_turn=False)

    # Step 4: Format and return response
    formatted_results = [
        {"title": metadata.get("title", "Unknown Title"), "summary": doc}
        for doc, metadata_list in zip(results["documents"], results["metadatas"])
        for metadata in metadata_list
    ]

    return {
        "query": q,
        "category": category,
        "results": formatted_results,
        "llm_response": llm_response,
    }
