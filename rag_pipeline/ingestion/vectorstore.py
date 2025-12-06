import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# Initializing Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

INDEX_NAME = "checkmyexams-prod" #we can change this later
DIMENSION = 1536 # dimension of the embedding model we're using. Vector DB and embedding model should have the same dimension
REGION = "us-east-1"

def get_index():
    """Returns a Pinecone index, creating it if it doesn't exist"""
    if not pc.has_index(INDEX_NAME):
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=REGION)
        )
        print(f"Create Pinecone index: {INDEX_NAME}")
    else:
        print(f"Using existing index: {INDEX_NAME}")


    return pc.Index(INDEX_NAME)

def upsert_vectors(vectors: list):
    """Upserts a list of vectors into the Pinecone index"""
    index = get_index()
    index.upsert(vectors=vectors)
    print(f"Upserted {len(vectors)} vectors to index '{INDEX_NAME}'")

def delete_vectors(filter:dict):
    """Deletes vectors from the index that matches a metadata filter"""
    """This function will be useful when the user deletes a Study Space. We just find match the study_space_id with the stored vectors (in the metadata) and delete the vector"""
    index = get_index()
    index.delete(filer=filter)
    print(f"Deleted vectors matching {filter}")