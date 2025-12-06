import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_query_embedding(query: str, model: str = "text-embedding-3-small") -> list:
    """Returns a normalized embedding vector for the given user query."""
    response = client.embeddings.create(model=model, input=query)
    emb = np.array(response.data[0].embedding)
    emb = emb / np.linalg.norm(emb)  # normalizing for cosine similarity
    return emb.tolist()
