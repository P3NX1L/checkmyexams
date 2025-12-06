from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_text_into_chunks(text: str, chunk_size: int = 2000, chunk_overlap: int = 200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)
