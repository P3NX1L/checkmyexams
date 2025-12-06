from typing import List, Optional
from langchain.schema import Document
from app.rag_pipeline.ingestion.embedder import get_embedding
from app.rag_pipeline.ingestion.vectorstore import upsert_vectors
# def ingest_document(file_path: str, user_id: str, study_space_id:str, file_id: Optional[str] = None):
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



def ingest_document(documents: List[Document], user_id: str, study_space_id: str, file_id: str, namespace: Optional[str] = None):
    """
    Embeds already-prepared text chunks (LangChain Documents) and upserts them to Pinecone.
    This avoids redoing extraction and chunking.
    """
    
    vectors = []

    for i, doc in enumerate(documents):
        text = doc.page_content
        emb = get_embedding(text)

        clean_meta = {
            k: v
            for k, v in doc.metadata.items()
            if v is not None and v != "" and v != []
        }

        metadata = {
            **clean_meta,
            "user_id": user_id,
            "study_space_id": study_space_id,
            "file_id": file_id,
            "chunk_index": i,
            "text_preview": text[:400],
        }

        vectors.append({
            "id": f"{file_id}-chunk-{i}",
            "values": emb,
            "metadata": metadata
        })

    upsert_vectors(vectors, namespace=namespace)
    return {"file_id": file_id, "chunks_upserted": len(vectors)}
