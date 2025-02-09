import chromadb
from utils.config import config
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

"""
1.	Receive a query (q) and an optional category (category) from a request.
2.	Search ChromaDB for relevant documents using the query.
3.	Extract & format the results before returning them as JSON.
"""

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for now, restrict later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug before initializing ChromaDB
print("Initializing ChromaDB Client...")

# Initialize ChromaDB client and collection
try:
    chroma = config.get_section("chroma")
    print(f"ChromaDB Root Path: {chroma['root']}")
    client = chromadb.PersistentClient(path=chroma["root"])
    collection = client.get_or_create_collection(name=chroma["dbname"])
    
    # # Check if ChromaDB contains data
    # data = collection.get(limit=10)
    # if not data["ids"]:
    #     print("No collections found in the ChromaDB database.")
    # else:
    #     print("Found collections in ChromaDB:")
    #     for key, value in data.items():
    #         if key == 'documents':
    #             continue
    #         print(f"  {key}: {value}")

except Exception as e:
    print(f"ChromaDB Initialization Failed: {e}")


@app.get("/search")
async def search(q: str = Query(..., description="Search query"), category: str=None):
    print(f"Searching ChromaDB: Query: '{q}', Category: '{category}'")

    # Query ChromaDB for relevant results
    results = collection.query(
        query_texts=[q],
        n_results=2,
        include=["documents", "metadatas"]
    )

    print(results)
    print(results.keys())

    # Extract relevant data
    formatted_results = []
    for idx, (doc, metadata_list) in enumerate(zip(results["documents"], results["metadatas"])):
        # Ensure metadata is correctly accessed (metadata_list is a list, extract first item)
        metadata = metadata_list[0] if isinstance(metadata_list, list) and metadata_list else {}

        formatted_results.append({
            "id": idx,
            "title": metadata.get("title", "Unknown Title"),  # Use get() to avoid key errors
            "summary": doc
        })

    print("ChromaDB Results:", formatted_results)

    return {"query": q, "category": category, "results": formatted_results}