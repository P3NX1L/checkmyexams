import os
from dotenv import load_dotenv
from pinecone import Pinecone
from rag_pipeline.retrieval.query_embedder import get_query_embedding

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = "checkmyexams-prod"

def query_index(
    query_text: str,
    user_id: str = None,
    study_space_id: str = None,
    file_id: str = None,
    top_k: int = 5
):
    """
    Searches Pinecone for top-k chunks relevant to a user query.
    Filters by user_id, study_space_id, or file_id if provided.
    """
    index = pc.Index(INDEX_NAME)
    query_vector = get_query_embedding(query_text)

    # building metadata filter dynamically
    filter_dict = {}
    if user_id:
        filter_dict["user_id"] = user_id
    if study_space_id:
        filter_dict["study_space_id"] = study_space_id
    if file_id:
        filter_dict["file_id"] = file_id

    print(f"Querying index '{INDEX_NAME}' with filters: {filter_dict or 'None'}")

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict if filter_dict else None
    )

    matches = results.get("matches", [])
    print(f"Retrieved {len(matches)} matches.")
    return matches
