import os
from dotenv import load_dotenv
from pinecone import Pinecone
from app.rag_pipeline.retrieval.query_embedder import get_query_embedding
from typing import Any, Dict, List, Optional

# Load .env for Pinecone credentials
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "checkmyexams-prod")
MIN_SIMILARITY_SCORE = float(os.getenv("MIN_SIMILARITY_SCORE", 0.01))

if not PINECONE_API_KEY:
    raise EnvironmentError("Missing PINECONE_API_KEY in environment variables.")

# Initialize Pinecone client
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to initialize Pinecone index: {str(e)}")

def query_index(
    query_text: str,
    user_id: Optional[str] = None,
    study_space_id: Optional[str] = None,
    file_id: Optional[str] = None,
    top_k: int = 5,
    namespace: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query Pinecone for top-k relevant chunks for a given query.
    Filters by user_id, study_space_id, and file_id (optional).
    """
    if not query_text or not query_text.strip():
        raise ValueError("Query text cannot be empty.")

    

    # Execute Pinecone vector search
    try:
        #generate query embedding
        query_vector = get_query_embedding(query_text)

        response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace or "",
        )

        # Filter out low-scoring matches
        matches = [
            match for match in response.get("matches", [])
            if match.get("score", 0) >= MIN_SIMILARITY_SCORE
        ]

        print(f"[Retrieval] Retrieved {len(matches)} matches for query: '{query_text}'.")
        return matches
    
    except Exception as e:
        raise RuntimeError(f"Pinecone query failed: {str(e)}")