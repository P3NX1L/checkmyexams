"""
Frontend use example:

await fetch("http://localhost:8000/ai/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question_latex: "...",
    correct_answer_latex: "...",
    explanation_latex: "...",
    marks: 5,
    topic: "Physics",
    student_answer: "Force equals mass times acceleration",
    comment: "Good effort, but missing details about direction of force.",
    user_message: "Can you explain why acceleration changes with mass?",
    session_id: "student_001"
  })
});
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import os, json, logging, asyncio
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai

from app.utils import cache_manager

# Setup
router = APIRouter()
LOG_DIR = "app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

load_dotenv(find_dotenv())

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "ask_ai_trigger.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# In-memory chat sessions
chat_sessions = {}

# Models
class ChatRequest(BaseModel):
    question_latex: str
    correct_answer_latex: str
    explanation_latex: str
    marks: float
    topic: str
    student_answer: str
    comment: str
    user_message: str
    session_id: Optional[str] = "default"
    user_id: str
    study_space_id: str
    namespace: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

# SERIALIZABLE JSON ERROR TRYING
def make_history_json_safe(history):
    safe = []
    for item in history:
        safe.append({
            "role": item.get("role"),
            "parts": [
                {"text": p.text if hasattr(p, "text") else p.get("text")}
                for p in item.get("parts", [])
            ]
        })
    return safe


# Prompt Builder
def build_educational_prompt(request: ChatRequest) -> str:
    return f"""You are an educational AI assistant for the test prep platform "CheckMyExams" helping students learn across all subjects.

AVAILABLE CONTEXT:
Topic: {request.topic}
Marks Available: {request.marks}
Question: {request.question_latex}
Correct Answer: {request.correct_answer_latex}
Explanation: {request.explanation_latex}
Student's Answer: {request.student_answer}
Teacher's Comment: {request.comment}

STUDENT SAYS: {request.user_message}

FORMAT RULES:
- Use proper markdown formatting and LaTeX for math ($...$)
- Keep answers short, clear, and visually structured
- Use • for bullet points and numbered lists when needed
- Be friendly, encouraging, and concise

RESPONSE INSTRUCTIONS:
- Greet if user greets
- If a specific question: answer directly in 1–3 sentences
- Explain further only when explicitly asked
- Never return code fences or markdown syntax outside formatting
- Keep tone educational and motivational
"""

async def send_to_gemini(prompt: str, session_id: str) -> str:
    try:
        if session_id not in chat_sessions:
            chat_sessions[session_id] = model.start_chat(history=[])

        chat = chat_sessions[session_id]
        response = await asyncio.to_thread(chat.send_message, prompt, stream=False)
        return response.text.strip()

    except Exception as e:
        logging.error(f"[GEMINI ERROR] Session={session_id} | {e}")
        raise HTTPException(status_code=500, detail="Error generating AI response")

# Endpoint: Ask AI Chat
@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Handles chat messages between the student and the AI assistant.
    Keeps conversation context within a session and saves chat logs.
    """
    try:
        prompt = build_educational_prompt(request)
        response_text = await send_to_gemini(prompt, request.session_id)

        # Save chat in memory session history
        if request.session_id in chat_sessions:
            chat_sessions[request.session_id].history.append(
                {"role": "user", "parts": [{"text": request.user_message}]}
            )
            chat_sessions[request.session_id].history.append(
                {"role": "model", "parts": [{"text": response_text}]}
            )

        # Cache save (Save Chat button support)
        chat_hash = f"chat_{request.session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        chat_data = {
            "hash": chat_hash,
            "session_id": request.session_id,
            "topic": request.topic,
            "question": request.question_latex,
            "student_answer": request.student_answer,
            "user_message": request.user_message,
            "response": response_text,
            "history": make_history_json_safe(chat_sessions[request.session_id].history),
            "timestamp": datetime.now().isoformat(),
        }

        background_tasks.add_task(cache_manager.write_cache, chat_hash, chat_data)
        logging.info(f"[CHAT SAVED] Session={request.session_id} | Topic={request.topic}")

        return ChatResponse(response=response_text, session_id=request.session_id)

    except Exception as e:
        logging.exception(f"[CHAT ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint: Save Chat Manually
@router.post("/save")
async def save_chat(session_id: str):
    """Triggered by frontend 'Save Chat' button."""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        chat_hash = f"chat_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        chat_data = {
            "hash": chat_hash,
            "session_id": session_id,
            "history": chat_sessions[session_id].history,
            "saved_at": datetime.now().isoformat(),
        }

        cache_manager.write_cache(chat_hash, chat_data)
        logging.info(f"[CHAT MANUAL SAVE] Session={session_id} saved manually")

        return {"status": "success", "hash": chat_hash, "message": "Chat saved successfully"}

    except Exception as e:
        logging.error(f"[SAVE ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to save chat")

# Endpoint: Manage Sessions
@router.get("/sessions")
async def list_sessions():
    return {
        "active_sessions": list(chat_sessions.keys()),
        "count": len(chat_sessions)
    }

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        logging.info(f"[SESSION DELETED] {session_id}")
        return {"message": f"Session {session_id} deleted successfully"}
    raise HTTPException(status_code=404, detail="Session not found")
