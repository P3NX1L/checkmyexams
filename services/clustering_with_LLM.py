import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key missing")

client = OpenAI(api_key=api_key)

# Extracts topics from the output of topics extractor
def extract_topic_dicts(results_json: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extracting a list of dictionaries where each dictionary maps topic -> summary.
    """
    topic_dicts = []
    for entry in results_json.get("results", []):
        topics = entry.get("topics", [])
        if topics:
            topic_map = {t["topic"]: t["summary"] for t in topics if "topic" in t and "summary" in t}
            topic_dicts.append(topic_map)
    return topic_dicts

# Sending the multiple topic -> summary dictionaries to GPT mini model for clustering same but differently worded topics
def cluster_similar_topics(topic_dicts: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Sends topic dictionaries to GPT to merge worded-differently duplicates.
    Returns a JSON dictionary mapping grouped topic -> summarized description.
    """
    if not topic_dicts:
        raise ValueError("No topic dictionaries found in input JSON.")

    # preparing the text for the LLM
    input_text = "\n\n".join(
        [f"Dictionary {i+1}:\n" + "\n".join([f"{k}: {v}" for k, v in d.items()])
         for i, d in enumerate(topic_dicts)]
    )

    prompt_old = f"""
You are a highly intelligent clustering model.
You will receive several dictionaries, each mapping academic topics to summaries.
Group similar topics into one topic.
For each grouped topic, write a short summary of what those grouped topics cover in total.

Return your answer ONLY as a valid JSON dictionary
where each key is a topic name and each value is its summary.

Special instructions:
Group only same topics which are worded differently.
Topics that are even slightly different should be considered separate.

Here are the dictionaries:

{input_text}
"""
    prompt = f"""
        You are a topic clustering model.
        You will receive several dictionaries, each mapping topics to summaries, one dictionary per file.

        Group similar or same-meaning topics together into clusters.
        For each cluster:
        - Provide a short combined summary.
        - List the files (by index number) that contained those topics.

        Return ONLY valid JSON in this exact format:
        {{
        "clusters": {{
            "Cluster Topic Name": {{
            "summary": "Merged summary of that topic",
            "files": ["file1.pdf", "file2.pdf"]
            }}
        }}
        }}

        Do not include any text outside JSON.

        Here are the topic dictionaries:

        {input_text}
        """
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    output_text = response.choices[0].message.content.strip()

    if output_text.startswith("```json"):
        output_text = output_text.replace("```json", "").strip("` \n")
    if output_text.endswith("```"):
        output_text = output_text.rstrip("` \n")

    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        print("GPT output not valid JSON. Raw output below:")
        print(output_text)
        return {"error": "Invalid JSON output", "raw_response": output_text}


# WRAPPER FUNCTION FOR PIPELINE INTEGRATION
def cluster_topics_pipeline(results_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integrates topic clustering into the processing pipeline.
    Takes topic-extraction JSON and returns grouped topics.
    """
    topic_dicts = extract_topic_dicts(results_json)
    if not topic_dicts:
        print(" No topics extracted from input JSON.")
        return {}

    clustered = cluster_similar_topics(topic_dicts)
    return clustered
