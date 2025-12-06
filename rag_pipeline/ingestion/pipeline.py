def ingest_document(file_path: str, user_id: str, study_space_id:str, file_id: Optional[str] = None):
    """Ingests a document into the Pinecone index:
    1. Extracts text from file
    2. Splits into chunks
    3. Embeds each chunk
    4. Upserts to Pinecone with metadata


    Upserting:
    vectors = []
    for i, chunk in enumerate(chunks):
        emb = get_embedding(chunk)
        vectors.append({
            "id": f"{user_id}-{file_id}-chunk-{i}",
            "values": emb,
            "metadata": {
                "user_id": user_id,
                "file_id": file_id,
                "study_space_id": study_space_id,
                "chunk_index": i,
                "text": chunk
            }
        })"""