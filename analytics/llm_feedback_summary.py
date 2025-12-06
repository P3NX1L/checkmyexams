import os
import json
import asyncio
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai


# Load model
load_dotenv(find_dotenv())
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GOOGLE_MODEL", "gemini-2.5-pro")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logging.warning("GEMINI_API_KEY missing. LLM-based feedback will fallback.")



# Low-level LLM calling layer
async def _call_llm_async(prompt: str) -> str:
    def run():
        model = genai.GenerativeModel(MODEL_NAME)
        res = model.generate_content(prompt)
        return res.text.strip()

    return await asyncio.to_thread(run)


def call_llm_sync(prompt: str, retries=2) -> str:
    last = None
    for attempt in range(1, retries + 1):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            out = loop.run_until_complete(_call_llm_async(prompt))
            loop.close()
            return out
        except Exception as e:
            last = e
            logging.error(f"[LLM] Attempt {attempt} failed: {e}")

    raise last



# Shared JSON cleaning logic
def _clean_llm_json(raw: str) -> Dict[str, Any]:
    raw = raw.strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except Exception:
        logging.error("[LLM] Invalid JSON from LLM.\nRaw:\n" + raw)
        return {}


# Base prompt builder
def build_prompt(topic: str,
                 topic_stats: Dict[str, Any],
                 last_n_feedback: List[Dict[str, Any]],
                 previous_summary: Dict[str, Any],
                 instruction: str) -> str:

    return f"""
You are a student analytics model.

Your task: {instruction}

You must produce a STRICT JSON object only. No markdown.

Context:
Topic: {topic}

Topic Stats:
{json.dumps(topic_stats, indent=2)}

Previous Summary:
{json.dumps(previous_summary, indent=2)}

Recent Feedback Entries (last N):
{json.dumps(last_n_feedback, indent=2)}

Rules:
- Use only the details above.
- Keep each list item short, fact-based, student-friendly.
- Provide 3–4 bullets maximum unless impossible.
- Output only valid JSON.
"""



# High-level LLM functions
def generate_topic_feedback_summary(topic: str,
                                    topic_stats: Dict[str, Any],
                                    last_n_feedback: List[Dict[str, Any]],
                                    previous_summary: Dict[str, Any]) -> Dict[str, Any]:

    if not GEMINI_API_KEY:
        return {"strengths": [], "needs_attention": []}

    prompt = build_prompt(
        topic=topic,
        topic_stats=topic_stats,
        last_n_feedback=last_n_feedback,
        previous_summary=previous_summary,
        instruction="Generate a JSON with 'strengths' and 'needs_attention' each containing 2–4 bullet points."
    )

    raw = call_llm_sync(prompt)
    parsed = _clean_llm_json(raw)

    strengths = parsed.get("strengths", [])
    needs = parsed.get("needs_attention", [])

    return {
        "strengths": strengths[:4],
        "needs_attention": needs[:4],
    }


def generate_topic_strengths(topic: str,
                             topic_stats: Dict[str, Any],
                             last_n_feedback: List[Dict[str, Any]],
                             previous_summary: Dict[str, Any]) -> List[str]:

    prompt = build_prompt(
        topic,
        topic_stats,
        last_n_feedback,
        previous_summary,
        instruction="Generate only a JSON with field 'strengths': a list of 2–4 strengths."
    )

    raw = call_llm_sync(prompt)
    parsed = _clean_llm_json(raw)

    strengths = parsed.get("strengths", [])
    return strengths[:4]


def generate_topic_weak_points(topic: str,
                               topic_stats: Dict[str, Any],
                               last_n_feedback: List[Dict[str, Any]],
                               previous_summary: Dict[str, Any]) -> List[str]:

    prompt = build_prompt(
        topic,
        topic_stats,
        last_n_feedback,
        previous_summary,
        instruction="Generate only a JSON with field 'weak_points': a list of 2–4 weaknesses."
    )

    raw = call_llm_sync(prompt)
    parsed = _clean_llm_json(raw)

    weak_points = parsed.get("weak_points", [])
    return weak_points[:4]


def generate_subject_level_summary(subject: str,
                                   topic_stats_all: Dict[str, Any]) -> Dict[str, Any]:

    prompt = f"""
Summarize the overall student performance in subject '{subject}' using STRICT JSON:
{json.dumps(topic_stats_all, indent=2)}

Output:
{
  "overall_strengths": [...],
  "overall_needs_attention": [...]
}

Rules:
- Each list must contain 2–4 concise bullet points.
- No markdown or text outside JSON.
"""

    raw = call_llm_sync(prompt)
    parsed = _clean_llm_json(raw)

    return {
        "overall_strengths": parsed.get("overall_strengths", [])[:4],
        "overall_needs_attention": parsed.get("overall_needs_attention", [])[:4],
    }
