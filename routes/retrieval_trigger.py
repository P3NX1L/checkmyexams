from fastapi import APIRouter, HTTPException, Query
from app.rag_pipeline.retrieval.pipeline import retrieve_answer

router = APIRouter()

# from the frontend side, the namespace should be extracted from the uploaded files always for filter.
@router.get("/query")
async def retrieve_query(
    query_text: str = Query(..., description="User question or search query"),
    user_id: str = Query(None, description="Optional user ID filter(optional)"),
    study_space_id: str = Query(..., description="Optional study space filter(optional)"),
    file_id: str = Query(None, description="Optional file filter(optional)"),
    top_k: int = Query(5, description="Number of top results to return"),
    namespace: str = Query(..., description="Mention the namespace")
):
    try:
        results = retrieve_answer(
            query_text=query_text,
            user_id=user_id,
            study_space_id=study_space_id,
            file_id=file_id,
            top_k=top_k,
            namespace=namespace
        )

        return {
            "query": query_text,
            "count": len(results),
            "results": results,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
