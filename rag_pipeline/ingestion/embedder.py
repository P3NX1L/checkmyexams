import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Initializing openai client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Generate normalized embedding
def get_embedding(text: str, model: str = "text-embedding-3-small") -> list:
    """Returns a normalized embedding vector for a given chunk"""
    response = client.embeddings.create(model=model, input=text)
    emb = np.array(response.data[0].embedding)
    emb = emb / np.linalg.norm(emb) # normalizing for cosine similarity
    return emb.tolist()