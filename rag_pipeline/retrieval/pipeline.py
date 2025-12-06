## HAVE TO ASK....WHICH SUPABASE TABLE TO TARGET TO FETCH THE STUDY SPACE ID -> TO UPSERT THE ID TO THE PINECONE WHILE INGESTION
# AND GETTING RESULTS FROM THE RETRIEVAL(STUDY SPACE ID)

## WHEN USER UPLOADS THE SYLLABUS -> NEXT -> {MATHPIX_TRIGGER} -> SELECT TOPIC(S) -> CREATE -> {RG_TRIGGER}
# RAG_TRIGGER CONTAINS INGESTION LAYER..HENCE WE NEED THE STUDY SPACE ID BEFORE THAT. {FRONTEND STORES IT INTO THE SUPABASE -> BACKEND FETCHES}

## OR > AFTER CREATE BUTTON HIT, FRONTEND STORES IT INTO THE SUPABASE FIRST -> BACKEND FETCHES THE STUDY SPACE ID ->
#->  THEN PROCESSES

## NEEDS BACKEND UPDATION

## NAMESPACE -> STUDYSPACE ID as input for frontend. they have to test it

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

from app.rag_pipeline.retrieval.retriever import query_index
from app.rag_pipeline.retrieval.query_embedder import get_query_embedding


load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "checkmyexams-prod")
DEFAULT_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "default")

if not PINECONE_API_KEY:
    raise EnvironmentError("Missing PINECONE_API_KEY in environment variables.")


# Retrieval Pipeline

def retrieve_answer(
    query_text: str,
    user_id: Optional[str] = None,
    study_space_id: Optional[str] = None,
    file_id: Optional[str] = None,
    top_k: int = 5,
    namespace: Optional[str] = DEFAULT_NAMESPACE,
) -> List[Dict[str, any]]:
    """
    End-to-end retrieval orchestration for the RAG pipeline.

    Steps:
      1. Validate query and environment
      2. Generate query embedding
      3. Query Pinecone index
      4. Format results for output

    Args:
        query_text (str): The user's search query.
        user_id (str, optional): Filter results for a specific user.
        study_space_id (str, optional): Filter results for a specific study space.
        file_id (str, optional): Filter results for a specific file.
        top_k (int): Number of top matches to return.
        namespace (str): Pinecone namespace (default: "default").

    Returns:
        List[Dict[str, Any]]: Structured list of relevant chunks with metadata.
    """

    if not query_text or not query_text.strip():
        raise ValueError("Query text cannot be empty.")

    print(f"[Retrieval Pipeline] -> Starting retrieval for query: '{query_text}'")

    # Step 2: Generate query embedding
    try:
        query_embedding = get_query_embedding(query_text)
    except Exception as e:
        raise RuntimeError(f"Query embedding generation failed: {str(e)}")

    # Step 3: Query Pinecone via retriever
    try:
        matches = query_index(
            query_text=query_text,
            user_id=user_id,
            study_space_id=study_space_id,
            file_id=file_id,
            top_k=top_k,
            namespace=namespace,
        )
    except Exception as e:
        raise RuntimeError(f"Pinecone retrieval failed: {str(e)}")


    # Step 4: Format results

    results = [
        {
            "id": match.get("id"),
            "score": match.get("score"),
            "text": match.get("metadata", {}).get("text_preview", ""),
            "file_id": match.get("metadata", {}).get("file_id", ""),
            "study_space_id": match.get("metadata", {}).get("study_space_id", ""),
        }
        for match in matches or []
    ]

    # Step 5: Logging and output

    if not results:
        print("[Retrieval Pipeline] No matches found. Try a broader query or check namespace.")
    else:
        print(f"[Retrieval Pipeline] ✅ Retrieved {len(results)} results from index '{PINECONE_INDEX_NAME}'.")

    return results
