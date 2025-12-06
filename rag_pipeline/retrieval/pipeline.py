from rag_pipeline.retrieval.retriever import query_index

def retrieve_answer(
        query_text: str,
        user_id: str = None,
        study_space_id: str = None,
        file_id: str = None,
        top_k: int = 5
):
    """
    Runs the retrieval pipeline:
    1. Embeds the query
    2. Searches Pinecone
    3. Returns the top matching chunks and scores
    """
    print(f"User query: {query_text}")

    matches = query_index(
        query_text=query_text,
        user_id=user_id,
        study_space_id=study_space_id,
        file_id=file_id,
        top_k=top_k
    )

    formatted_results = [
        {
            "score": match["score"],
            "text": match["metadata"].get("text", ""),
            "file_id": match["metadata"].get("file_id"),
            "study_space_id": match["metadata"].get("study_space_id"),
        }
        for match in matches
    ]

    if not formatted_results:
        print("No results found.")
    else:
        print(f"Top {len(formatted_results)} results ready.")

    return formatted_results
