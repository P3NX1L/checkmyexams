# instead of loading .env everytime, we can load it once...
# this helps in keeping main code clean - if we want to change api sources later like moving to AWS secrets manager or something else.


import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

if not PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY in .env")
