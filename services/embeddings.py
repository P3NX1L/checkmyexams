# seperating the embedding setup....to be used easily for other file types

import time
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from app.config import PINECONE_API_KEY

def setup_pinecone(documents, index_name, namespace):
    pc = Pinecone(api_key=PINECONE_API_KEY)
    embeddings = PineconeEmbeddings(model='multilingual-e5-large')
    spec = ServerlessSpec(cloud='aws', region='us-east-1')

    if index_name not in pc.list_indexes().names():
        pc.create_index(index_name, dimension=embeddings.dimension, metric="cosine", spec=spec)
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
    
    store = PineconeVectorStore.from_documents(
        documents=documents,
        index_name=index_name,
        embedding=embeddings,
        namespace=namespace
    )
    return store
