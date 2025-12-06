
import re
from tqdm.auto import tqdm
from langchain.schema import Document
from spacy.lang.en import English

nlp = English()
nlp.add_pipe("sentencizer")

#Normalize whitespace, remove line breaks.
def text_formatter(text: str) -> str:
    text = text.replace("\xa0", " ")  # non-breaking space
    text = re.sub(r'\s+', ' ', text)
    
    text = re.sub(r'\.([A-Z])', r'. \1', text)  # ensure space after periods
    return text.strip()

#Split each page text into pages using spacy.
'''
def split_sentences(text_pages):
    
    for page in tqdm(text_pages, desc="Splitting sentences"):
        sentences = [str(s) for s in nlp(page["text"]).sents]
        page["sentences"] = sentences
    return text_pages
'''
#split file into sentences using spacy
'''
def split_sentences(text_pages):
    all_text = " ".join([page["text"] for page in text_pages])
    sentences = [str(s) for s in nlp(all_text).sents]
    return sentences
'''

#split file using regex
'''
def split_sentences(text):
    text = re.sub(r'\s+', ' ', text)
    return re.split(r'(?<=[.!?])\s+', text)
'''
def split_words(text):
    text = re.sub(r'\s+', ' ', text)  # normalize
    return text.strip().split()


#Combine sentences into chunks of specified size.
# Combine sentences into chunks of approx 300 words (not 10 sentences).
#overlapping solves the context split problem - the LLM model can't see the full picture unless it retreives both chunks. 
# so overlapping a small amount of 50 words will produce better results. 

'''
def create_chunks(sentences, max_words=300, overlap=50):
    chunks = []
    current_words = []
    current_len = 0

    for sent in sentences:
        sent_words = sent.split()
        current_words.extend(sent_words)
        current_len += len(sent_words)

        if current_len >= max_words:
            chunk_text = " ".join(current_words).strip()
            chunks.append({
                "sentence_chunk": chunk_text,
                "chunk_token_count": len(current_words)
            })

            # Prepare overlap
            overlap_start = max(0, current_len - overlap)
            current_words = current_words[overlap_start:]
            current_len = len(current_words)

    # Final chunk
    if current_words:
        chunk_text = " ".join(current_words).strip()
        chunks.append({
            "sentence_chunk": chunk_text,
            "chunk_token_count": len(current_words)
        })

    return chunks
'''
def create_chunks(words, max_words=300, overlap=50):
    chunks = []
    step = max_words - overlap

    for i in range(0, len(words), step):
        chunk_words = words[i : i + max_words]
        if not chunk_words:
            continue

        chunk_text = " ".join(chunk_words)
        chunks.append({
            "sentence_chunk": chunk_text,
            "chunk_token_count": len(chunk_words)
        })

    return chunks


# Add this helper before chunks_to_documents

def normalize_chunks(chunks):
    """Ensure chunks are plain text strings."""
    normalized = []
    for ch in chunks:
        if isinstance(ch, dict) and "text" in ch:
            normalized.append(ch["text"])
        elif isinstance(ch, str):
            normalized.append(ch)
    return normalized

#Convert chunks to LangChain Document objects.
def chunks_to_documents(chunks, min_tokens=30, filename="file"):

    docs = []
    for i, c in enumerate(chunks):
        if c["chunk_token_count"] < min_tokens:
            continue
        docs.append(Document(
            page_content=c["sentence_chunk"],
            metadata={
                "chunk_id": i,
                "source": filename,
                
            }
        ))
    return docs
