"""

Frontend use: you can trigger this api by
await fetch("localhost:8000/rag/process", {
  method: "POST"
});
"""
'''
You can hit /status/<hash> 
from frontend to show progress while Gemini is processing multiple chunks.
'''

from fastapi import APIRouter, BackgroundTasks, UploadFile, File
import os, asyncio, datetime, logging
from concurrent.futures import ThreadPoolExecutor
from app.utils import cache_manager
from app.services import text_processing
from app.rag_pipeline.ingestion.pipeline import ingest_document
from app.services.text_extraction import (
    pdf_extraction, docx_extraction, pptx_extraction,
    xlsx_extraction, md_extraction, txt_extraction
)
from app.services import data_cleaner
import tempfile, shutil
import hashlib
from typing import List


router = APIRouter()
LOG_DIR = "app/logs"
os.makedirs(LOG_DIR, exist_ok=True)
executor = ThreadPoolExecutor(max_workers=6) 

logging.basicConfig(
    filename=os.path.join(LOG_DIR, f"rag_trigger.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def async_dump_cache(file_hash: str):
    """Background dump operation to archive cache after ingestion."""
    await asyncio.sleep(0.2)
    cache_manager.move_cache_to_dump(file_hash)

async def extract_and_cache_single_file(file: UploadFile):
    """
    Extract text from a single uploaded file, clean it, write to cache,
    and return the cache data that RAG needs.
    """

    extractors = {
        "pdf": pdf_extraction.extract_text_from_pdf,
        "docx": docx_extraction.extract_text_from_docx,
        "pptx": pptx_extraction.extract_text_from_pptx,
        "ppt": pptx_extraction.extract_text_from_pptx,
        "xlsx": xlsx_extraction.extract_text_from_xlsx,
        "md": md_extraction.extract_text_from_md,
        "txt": txt_extraction.extract_text_from_txt,
    }

    ext = file.filename.split(".")[-1].lower()
    if ext not in extractors:
        return {"error": f"Unsupported file {file.filename}"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        pages = extractors[ext](tmp_path)
        full_text = "".join(
            p.get("text", "") if isinstance(p, dict) else str(p)
            for p in pages
        )

        

        cleaned = data_cleaner.clean_text(full_text)
        formatted = text_processing.text_formatter(cleaned)

        # compute hash
        with open(tmp_path, "rb") as rf:
            file_hash = hashlib.sha256(rf.read()).hexdigest()

        cache_data = {
            "file": file.filename,
            "full_text": formatted,
            "hash": file_hash,
            "cached_at": datetime.datetime.now().isoformat()
        }

        cache_manager.write_cache(file_hash, cache_data)
        return cache_data

    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


async def process_cached_file(cache_data: dict, study_space_id: str, namespace: str, userid: str):
    """RAG pipeline for a single cached file."""
    try:
        file_hash = cache_data["hash"]
        text = cache_data.get("full_text") or cache_data.get("text") 
        
        # Skip large-file logic (no longer needed)
        logging.info(f"[INGEST] Processing file {cache_data.get('file')} normally (chunk size: ~300 words)")


        if not text or len(text.split()) < 50:
            logging.warning(f"[SKIPPED] Not enough text content for {cache_data.get('file')}")
            return None

        '''
        # Chunk + embed + store
        page_objs = [{"text": text, "page_number": 1}]
        page_objs = text_processing.split_sentences(page_objs)
        #page_objs = text_processing.split_words(page_objs)
        chunks = text_processing.create_chunks(page_objs)
       '''
        
        # Combine text (already a single string)
        all_text = text

        # Split into words (fast)
        words = text_processing.split_words(all_text)
        print("WORD COUNT:", len(words))
        # Chunk by word count
        chunks = text_processing.create_chunks(
            words,
            max_words=300,
            overlap=50
        )

        docs = text_processing.chunks_to_documents(chunks, filename=cache_data["file"])


        ingest_document(
            documents=docs,
            user_id=userid,
            study_space_id=study_space_id,
            file_id=file_hash,
            namespace=namespace,
            
        )

        
        # Construct the ingestion result with full details
        result = {
            "file": cache_data["file"],
            "hash": file_hash,
            "chunks": len(chunks),
            "status": "✅ Ingested successfully",
            "vector_count": len(docs),
            "timestamp": datetime.datetime.now().isoformat(),
        }

        #  Persist enriched cache
        cache_manager.write_cache(file_hash, result)
        logging.info(f"[RAG DONE] {cache_data['file']} ({len(chunks)} chunks)")
        return result


    except Exception as e:
        logging.error(f"[RAG ERROR] {cache_data.get('file')}: {e}")
        return {"file": cache_data.get("file"), "error": str(e)}

#SINCE WE ARE NOT USING LARGE FILE HANDLER FOR TOPICS EXTRACTIONS, WE NO LONGER NEED THE LOGIC FOR IT. LARGE_FILE_HANDLER IS SAFELY PRESENT IN /BIN FOLDER IF NEEDED IN FUTURE.
'''
@router.get("/status/{file_name}")
async def get_large_rag_status(file_name: str):
    folder = os.path.join("app/cache/chunks", file_name)
    if not os.path.exists(folder):
        return {"message": "No processing data found."}
    chunks = [f for f in os.listdir(folder) if f.endswith(".json")]
    return {"file": file_name, "processed_chunks": len(chunks)}
'''

@router.post("/process")
async def process_all_cached(background_tasks: BackgroundTasks, study_space_id: str, namespace: str, userid: str, files: List[UploadFile] = File(...)):

    """
    Upload + extract + process + ingest into vector store.
    """
    cache_entries = []

    for file in files:
        cache_data = await extract_and_cache_single_file(file)
        if "error" in cache_data:
            logging.error(f"[EXTRACTION ERROR] {file.filename}: {cache_data['error']}")
            continue
        cache_entries.append(cache_data)

    async def process_cached(c):
        result = await process_cached_file(c,study_space_id, namespace, userid)
        if result and "hash" in result:
            background_tasks.add_task(async_dump_cache, result["hash"])
        return result

    tasks = [process_cached(c) for c in cache_entries]
    results = await asyncio.gather(*tasks)

    return {
        "total_files": len(cache_entries),
        "results": results,
    }
