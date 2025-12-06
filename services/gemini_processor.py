# isolating LLM from the main code gives us the freedom to switch to another LLM in future or change our logic
# this is also helpful with switching to dynamic prompt creation in future version releases (BETA).

import json
import re
import google.generativeai as genai
from fastapi import HTTPException
from app.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    )
)

async def process_with_gemini(text: str, subject: str) -> list:
    prompt = f"""You're an expert at identifying the academic topics that are in a text file and extracting them for the student to study those topics for their exam.
    The topics that you extract should be relevant to what might come on the student's exam
    The topics should be broad **but not too broad**

    Extract a list of academic {subject} topics from the given text.

    Return a JSON array. Each item should be an object with:
    - "topic": the academic math topic (concise but complete),
    - "summary": a brief explanation of what that topic covers.

    Guidelines:
    - The extracted topics should be the ones that are mentioned multiple times and are more likely to come in the student's exam
    - Topics should be broad but **not too broad**—if a subtopic is academically distinct, list it separately.
    - Only include **academic topics** (not examples, concepts, or tools unless they are widely studied as standalone topics).
    - Avoid redundancy or vague topics.
    - Keep topic names short **while preserving clarity**.
    - Do **not** use newlines (\\n) in the output.
    - Return **raw JSON only**, no extra text or formatting.
    - Also make sure that the topics are not too specific
    - Make sure all the topics you add to the list is taught in the file or is written as something that can come in a student's exam
    - The topic that you add to the list just something that is mentioned in the file but if the topic is a decent part of the file (meaning: mentioned more than certain times)

    Format:
    [
      {{
        "topic": "...",
        "summary": "..."
      }},
      ...
    ]
    """
    #print(prompt)
    try:
        # combining prompt with extracted text
        full_prompt = f"{prompt}\n\n{text[:20000]}"

        # Generate response using Gemini
        response = model.generate_content(full_prompt)
        raw_output = response.text.strip()

        # Log or print a small preview for debugging
        print(" Gemini raw output:", raw_output[:300])

        # Clean markdown fences and stray text
        cleaned = re.sub(r'```json|```', '', raw_output).strip()

        # Extract only the JSON array portion if Gemini wrapped it in text
        match = re.search(r'\[.*\]', cleaned, re.S)
        if not match:
            raise ValueError("No JSON array detected in Gemini output")

        json_str = match.group(0)
        data = json.loads(json_str)

        # Optional: sanitize text
        for d in data:
            if "topic" in d:
                d["topic"] = re.sub(r'\s+', ' ', d["topic"]).strip()
            if "summary" in d:
                d["summary"] = re.sub(r'\s+', ' ', d["summary"]).strip()

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini processing failed: {e}")
