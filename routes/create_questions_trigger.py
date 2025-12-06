"""
Frontend use:
await fetch("localhost:8000/questions/generate", {
  method: "POST",
  body: formData
});
"""

from fastapi import APIRouter, Form, HTTPException, BackgroundTasks
from typing import List, Optional
import logging, os, json, asyncio
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai

from app.rag_pipeline.retrieval.pipeline import retrieve_answer
from app.utils import cache_manager

# Setup
router = APIRouter()
LOG_DIR = "app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

load_dotenv(find_dotenv())

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "create_questions_trigger.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in .env")

genai.configure(api_key=GEMINI_API_KEY)



# Helper: Async Gemini call with retry
async def generate_with_gemini(prompt: str, retries: int = 2) -> str:
    """
    Generate content using Gemini 2.5 Pro with limited retries.
    """
    model = genai.GenerativeModel(
        "gemini-2.5-pro",
        generation_config={"response_mime_type": "application/json"}
    )

    for attempt in range(1, retries + 1):
        try:
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text.strip()
        except Exception as e:
            logging.error(f"[GEMINI ERROR] Attempt {attempt}: {e}")
            if attempt == retries:
                raise HTTPException(status_code=500, detail=f"Gemini failed after {retries} retries.")
            await asyncio.sleep(1.5)  # backoff before retry


# Route
@router.post("/generate")
async def generate_questions(
    background_tasks: BackgroundTasks,
    student_input: str = Form(..., description="Student description of study area or question focus"),
    num_questions: int = Form(5, description="Number of questions to generate"),
    difficulty: List[str] = Form(default=["Moderate"], description="Difficulty levels: Easy, Moderate, Hard"),
    topics: List[str] = Form(..., description="List of topics to focus on"),
    namespace: str = Form(..., description="Optional Pinecone namespace to filter context"),
    study_space_id: str = Form(..., description="Study space ID to search"),
    user_id: str = Form(..., description="User ID for retrieval"),
):
    """
    Generates exam-style LaTeX questions using Gemini, based on retrieved context.
    """
    try:
        # Retrieve relevant chunks from existing RAG pipeline
        retrieval_results = retrieve_answer(
            query_text=student_input,
            user_id=user_id,
            study_space_id=study_space_id,
            file_id=None,
            top_k=5,
            namespace=namespace,
        )

        # Extract relevant context text
        context_snippets = []
        for res in retrieval_results:
            text = res.get("text") or res.get("metadata", {}).get("text")
            source = res.get("source") or res.get("metadata", {}).get("source", "")
            if text:
                context_snippets.append(f"From {source}:\n{text}")

        if not context_snippets:
            logging.warning(f"[NO CONTEXT] No relevant context found for query: {student_input}")

        context_section = "\n\n".join(context_snippets[:5])
        difficulty_text = ", ".join(difficulty)

        # Build the question generation prompt
        
        # OLDER PROMPT
        '''
        prompt = f"""You are an expert academic question generator.

The student has described what they want to practice:
---
{student_input}
The output is a JSON array so all the formatted LaTeX and other text should be compatible with JSON
Write all the output text in LaTeX and make sure it is compatible with Mathjax because Mathjax is being used to render the output on a webpage
Don't include any links in your output
Create text based questions, don't include diagrams/graphs
The questions should be very relevant to the student's preferences
Don't write long questions or explanations
The correct answer should only have the answer no explanation
The short explanation should be concise and clear
---

Your task is to:
- Create questions for the topic: {topics}
- Create exam style questions for the student to practice
- Generate questions that match the specified difficulty level(s): {difficulty_text}
- If multiple difficulty levels are selected, distribute questions across those levels appropriately.

For each question, also estimate the number of marks based on how long and complex it is. Use 1 to 5 marks per question as a guideline:
- 1 mark: short objective or definition-based (typically Easy)
- 2–3 marks: small calculation or conceptual reasoning (typically Moderate)
- 4–5 marks: multi-step derivation, proof, or problem-solving (typically Hard)
----
{context_section}
---

Use this context only to understand the study material that the student has to be tested on
The main thing is that the student should understand the concepts and should be able to answer questions in exam
You should ask questions that will make sure that the student understands the topic: {topics[0]}.

**The questions should  be very clear and easy for the student to understand what the question is asking**
**The explanation should be very clear so that the student reading it easily understands it**

Based on this, generate **{num_questions}** exam-style questions matching the specified difficulty level(s).
Make sure that exactly **{num_questions}** exam-style questions are generated
Each question should be followed by:
- A clear explanation
- The correct answer
- An estimated marks value (1 to 5)
- The topic should be {topics}
- The difficulty level of the question (Easy, Moderate, or Hard)
- The explanation and final answer must be fully consistent

LaTeX Formatting Rules:
- Please ensure that the latex format is perfect so that it is rendered perfectly on the webpage. This is the most important thing in your output (Number 1 priority)
- Do not use LaTeX line-break commands such as \\newline, \\linebreak.  End the math block, add a blank line or plain-text period, then start a new sentence.
- Write apostrophes and all sentence punctuation **outside** math mode.
  End a sentence after the closing delimiter, e.g. \\(10\\,\\%\\). not \\(10\\,\\%.\\)
- Ensure every LaTeX fragment compiles in MathJax: use standard macros only, wrap math in $$ ... $$, place units outside math mode with \\,\\text{{}}, and double-escape all back-slashes so the JSON is valid.
- Double-escape every back-slash so the JSON loads without errors.
- Ensure that you NEVER outputs a back-slash outside math delimiters.
- Your first priority should be to create perfect Mathjax compatible renderable LaTeX

STYLE GUIDE FOR OUTPUT
• **Inline math:**  
  – Wrap short formulas inside sentences with  `\\( … \\)` (or `$ … $` if enabled).  
  – Do **not** start a new line before or after inline math.

• **Display math:**  
  – Use `\\[ … \\]` **only** for multi-line derivations or matrices that truly need vertical space.  
  – If you open `\\[`, close it immediately after the block—no blank lines inside.

• **Lists / steps:**  
  – Begin bullets with `- ` or `1.`; **never** with a dot (`.`).  
  – Put the entire step (text + any inline math) on the **same line**.  
  – No blank line between consecutive bullet items.

• **Paragraphs:**  
  – Ordinary sentences stay in one paragraph; insert a blank line only when you want a new paragraph.

Return the output as RAW JSON ONLY (no markdown, no formatting). Just return an array of objects in this format only:
[
 {{
   "question_latex": "...",
   "explanation_latex": "...",
   "correct_answer_latex": "...",
   "marks": 3,
   "topic": "{topics[0]}",
   "difficulty": "Moderate"
 }}
]"""
'''

        # NEW PROMPT
        prompt = f"""
You are an expert academic question generator.

The student has described what they want to practice:
---
{student_input}
---

OUTPUT RULES
- Return a RAW JSON array (no markdown, no extra text).
- All LaTeX must be MathJax-compatible.
- Escape all backslashes for JSON validity.
- No links, no diagrams, no graphs.
- Questions must be clear, concise, and exam-style.
- The explanation must be short and easy to understand.
- The correct answer must contain ONLY the final answer (no explanation).
- EXACTLY {num_questions} questions must be generated.

TOPIC ASSIGNMENT (CRITICAL — REQUIRED)
- You are given a list of topics: {topics}
- **Each question MUST have a topic value that is a SINGLE STRING selected from this list.**
- **Never assign the full list.**
- **Never output an array.**
- For each question, set:
  "topic": "<one topic from the topics list>"

DIFFICULTY RULES
- Use these difficulty levels: {difficulty_text}
- If multiple difficulty levels are provided, distribute questions appropriately.

MARKING SCHEME (1–5 marks)
- 1 mark: short objective/definition (Easy)
- 2–3 marks: small calculation/reasoning (Moderate)
- 4–5 marks: multi-step derivation/problem (Hard)

ADDITIONAL CONTEXT
---
{context_section}
---
Use this content only to understand the subject matter.

PRIMARY GOAL
Create questions that test conceptual understanding of: {topics[0]}
Questions must be very clear and understandable.

LATEX RULES
- Perfect MathJax compatibility is the #1 priority.
- Inline math: \\( ... \\)
- Display math: \\[ ... \\] only when necessary.
- No \\newline or \\linebreak.
- No backslashes outside math mode.
- Put punctuation outside math mode.
- Use standard macros only.
- Double-escape all backslashes for JSON.

OUTPUT FORMAT (STRICT)
Return ONLY this JSON shape:
[
  {{
    "question_latex": "...",
    "explanation_latex": "...",
    "correct_answer_latex": "...",
    "marks": 3,
    "topic": "<one topic from the topics list>",
    "difficulty": "Moderate"
  }}
]

NOW GENERATE:
- Exactly {num_questions} questions
- Exam-style
- Matching the selected difficulty level(s)
- Each with: question, explanation, answer, marks, topic, and difficulty
"""

        # Generate with Gemini
        logging.info(f"[PROMPT START] Generating {num_questions} questions for topics {topics}")
        output_text = await generate_with_gemini(prompt)

        # Clean up potential markdown formatting
        output_text = output_text.replace("```json", "").replace("```", "").strip()

        try:
            questions = json.loads(output_text)
        except json.JSONDecodeError as e:
            logging.error(f"[JSON PARSE ERROR] {e}")
            raise HTTPException(status_code=500, detail="Gemini output not valid JSON")

        # Cache results asynchronously
        file_hash = f"questions_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cache_data = {
            "hash": file_hash,
            "query": student_input,
            "topics": topics,
            "difficulty": difficulty,
            "count": len(questions),
            "generated_at": datetime.now().isoformat(),
            "questions": questions,
        }
        background_tasks.add_task(cache_manager.write_cache, file_hash, cache_data)

        logging.info(f"[GENERATION DONE] {len(questions)} questions for {topics}")

        return {
            "status": "success",
            "query": student_input,
            "topics": topics,
            "difficulty": difficulty,
            "count": len(questions),
            "results": questions,
        }

    except Exception as e:
        logging.exception(f"[QUESTION GENERATION ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))
