from fastapi import APIRouter, HTTPException
from supabase import create_client
import os
from dotenv import load_dotenv, find_dotenv

# Initialize Supabase client
load_dotenv(find_dotenv())
router = APIRouter(prefix="/analytics", tags=["Analytics"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY") or os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.get("/get/{user_id}/{study_space_id}/{subject}")
def get_analytics(user_id: str, study_space_id: str, subject: str):
    try:
        resp = (
            supabase.table("analytics")
            .select("*")
            .eq("user_id", user_id)
            .eq("study_space_id", study_space_id)
            .eq("subject", subject)
            .execute()
        )
        return resp.data[0] if resp.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
