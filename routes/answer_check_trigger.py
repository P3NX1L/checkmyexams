"""
Frontend use:
await fetch("localhost:8000/answers/check", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question_latex: "...",
    correct_answer_latex: "...",
    explanation_latex: "...",
    marks: 3,
    topic: "Physics",
    student_answer: "The student’s written answer..."
  })
});
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging, os, json, asyncio
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai
from app.analytics.service import update_analytics,update_feedback_analytics
from app.utils import cache_manager

# Setup
router = APIRouter()
LOG_DIR = "app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

load_dotenv(find_dotenv())

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "answer_check_trigger.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("GOOGLE_MODEL", "gemini-2.5-pro")

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY or GOOGLE_API_KEY in .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# Schema
class AnswerCheckRequest(BaseModel):
    question_latex: str
    correct_answer_latex: str
    explanation_latex: str
    marks: float
    topic: str
    student_answer: str

# Async Gemini call with retry
async def generate_with_gemini(prompt: str, retries: int = 2) -> str:
    for attempt in range(1, retries + 1):
        try:
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text.strip()
        except Exception as e:
            logging.error(f"[GEMINI ERROR] Attempt {attempt}: {e}")
            if attempt == retries:
                raise HTTPException(status_code=500, detail=f"Gemini failed after {retries} retries.")
            await asyncio.sleep(1.5)

# Endpoint
@router.post("/check")
async def check_answer(payload: AnswerCheckRequest):
    """
    Evaluate a student's answer for correctness and marks using Gemini.
    Returns a structured JSON feedback object.
    """
    try:
        # Build prompt (same logic as original)
        prompt = f"""
You are an exam evaluator.

You are given:
Question: {payload.question_latex}
Explanation: {payload.explanation_latex}
Topic: {payload.topic}

Now evaluate the student's answer and respond ONLY in JSON.
Make sure that you feedback is friendly towards the student

Student Answer: {payload.student_answer}
The student answer can have the same meaning said in a different way for it to be correct
Award marks to student's answer accordingly
Be very professional while checking the answer and be friendly when writing the feedback

Return the output as raw JSON only (no markdown, no formatting). Just return an array of objects in this format only:
{{
  "is_correct": true or false,
  "marks_obtained": number (out of {payload.marks}),
  "weak_topic": true or false,
  "topic": "{payload.topic}",
  "comment": "Brief feedback about what the student did wrong or right"
}}
"""

        logging.info(f"[PROMPT START] Evaluating answer for topic '{payload.topic}'")

        # Generate response
        raw_reply = await generate_with_gemini(prompt)

        # Clean response text
        raw_reply = raw_reply.replace("```json", "").replace("```", "").strip()

        try:
            feedback = json.loads(raw_reply)
        except json.JSONDecodeError:
            logging.error(f"[JSON ERROR] Invalid Gemini response: {raw_reply}")
            raise HTTPException(status_code=500, detail="Invalid JSON response from Gemini")
        
        # Analytics Update Integration (Supabase)
        try:

            # extract is_correct from Gemini feedback
            feedback_entry = feedback[0] if isinstance(feedback, list) else feedback

            marks_obtained = float(feedback_entry.get("marks_obtained", 0) or 0)
            weak_topic = bool(feedback_entry.get("weak_topic", False))
            comment = feedback_entry.get("comment", "")

            # TODO: replace with real authenticated values from frontend/session
            user_id = "test_user"
            study_space_id = "dev_space"
            subject = "Physics"       # or however you define subject
            topic = payload.topic     # frontend sends topic name


            # 1) Update analytics (subject + topic-level stats)
            analytics_result = update_analytics(
                user_id=user_id,
                study_space_id=study_space_id,
                subject=subject,
                topic=topic,
                marks_scored=marks_obtained,
                marks_possible=payload.marks,
            )

            # 2) Update feedback analytics (store comment + maintain summary)
            feedback_summary = update_feedback_analytics(
                user_id=user_id,
                study_space_id=study_space_id,
                subject=subject,
                comment=comment,
                weak_topic=weak_topic,
                marks_scored=marks_obtained,
                marks_possible=payload.marks,
            )

            logging.info(f"[ANALYTICS UPDATED] topic={payload.topic}")
        except Exception as e:
            logging.error(f"[ANALYTICS UPDATE ERROR] {e}")


        # Add metadata for caching
        result_hash = f"answercheck_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cache_data = {
            "hash": result_hash,
            "question": payload.question_latex,
            "student_answer": payload.student_answer,
            "topic": payload.topic,
            "marks_total": payload.marks,
            "feedback": feedback,
            "generated_at": datetime.now().isoformat(),
            "analytics": analytics_result,
            "feedback_summary": feedback_summary,
        }
        cache_manager.write_cache(result_hash, cache_data)

        logging.info(f"[ANSWER CHECKED] {payload.topic} | Result: {feedback}")

        return {
            "status": "success",
            "topic": payload.topic,
            "feedback": feedback
        }

    except Exception as e:
        logging.exception(f"[ANSWER CHECK ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))
