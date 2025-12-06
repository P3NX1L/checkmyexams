
#testing remaining for all the functionalities.

'''
meeting queries ->

##CORRECTIONS TO BE DONE : CODE SNIPPET IN UPDATE_FEEDBACK_SUMMARY() -> existing = resp.data[0]
we are assuming this will return only one row -> if for some reason user call .insert() twice or the client runs the function twice -> 
code blindly uses resp.data[0], which silently ignores the conflicting row and continues.-> conflicting user analytics/future LLM summaries being wrong
OR prevent hitting the insert button twice from frontend side -> this can also solve the issue. -> we can make sure of it on both side also for two layers of prevention
->.insert instead of update..... can be caused due to client side / network glitch / user double click / worker running twice etc
->-> backend side taken care of ✅

## WE CAN AVOID LOGGING IN PRODUCTION, EXPENSIVE, UNNECESSARY -> logging should be reserved for errors, warnings, critical errors

## LLM SUMMARY IS HAPPENING IN MAIN QUERY, -> WE CAN MOVE IT TO BACKGROUND TASK

'''
'''
ways to mimic the questions more precise.
'''


import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.analytics.llm_feedback_summary import generate_topic_feedback_summary

from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv
from app.analytics.history_logger import log_analytics_history


load_dotenv(find_dotenv())
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_API_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE_NAME = "analytics"

ALPHA = 0.3
FEEDBACK_SUMMARY_FREQUENCY = int(os.getenv("FEEDBACK_SUMMARY_FREQUENCY", "5"))
MAX_FEEDBACK_HISTORY = int(os.getenv("MAX_FEEDBACK_HISTORY", "200"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def update_analytics(
    user_id: str,
    study_space_id: str,
    subject: str,
    topic: str,
    marks_scored: float,
    marks_possible: float,
) -> Dict[str, Any]:

    try:
        resp = (
            supabase.table(TABLE_NAME)
            .select("*")
            .eq("user_id", user_id)
            .eq("study_space_id", study_space_id)
            .eq("subject", subject)
            .execute()
        )
        if len(resp.data) > 1:
            raise RuntimeError(
                f"DATA INTEGRITY ERROR: Duplicate analytics rows detected for user={user_id}, space={study_space_id}, subject={subject}"
            )


        recent_accuracy = (marks_scored / marks_possible) * 100 if marks_possible > 0 else 0.0

        if resp.data:
            existing = resp.data[0]

            total_questions = existing.get("total_questions", 0) + 1
            correct_answers = existing.get("correct_answers", 0)
            if abs(marks_scored - marks_possible) < 1e-6:
                correct_answers += 1

            prev_accuracy = existing.get("accuracy", 0.0)
            total_marks_scored = existing.get("total_marks_scored", 0.0) + marks_scored
            total_marks_possible = existing.get("total_marks_possible", 0.0) + marks_possible

            new_accuracy = ALPHA * recent_accuracy + (1 - ALPHA) * prev_accuracy

            progress_history = existing.get("progress_history") or []
            if not isinstance(progress_history, list):
                progress_history = []
            progress_history.append({
                "timestamp": _now_iso(),
                "topic": topic,
                "recent_accuracy": recent_accuracy,
                "previous_accuracy": prev_accuracy,
                "new_accuracy": new_accuracy,
                "marks_scored": marks_scored,
                "marks_possible": marks_possible,
            })

            topics = existing.get("topics") or {}
            if not isinstance(topics, dict):
                topics = {}

            topic_key = topic or "general"

            topic_stats = topics.get(topic_key) or {
                "total_questions": 0,
                "correct_answers": 0,
                "total_marks_scored": 0.0,
                "total_marks_possible": 0.0,
                "accuracy": 0.0,
            }

            previous_topic_accuracy = topic_stats.get("accuracy", 0.0)
            recent_topic_accuracy = (marks_scored / marks_possible) * 100 if marks_possible > 0 else 0

            new_topic_accuracy = ALPHA * recent_topic_accuracy + (1 - ALPHA) * previous_topic_accuracy

            # update counters
            topic_stats["total_questions"] += 1
            topic_stats["total_marks_scored"] += marks_scored
            topic_stats["total_marks_possible"] += marks_possible
            topic_stats["accuracy"] = new_topic_accuracy


            if marks_possible > 0 and abs(marks_scored - marks_possible) < 1e-6:
                topic_stats["correct_answers"] += 1

            topics[topic_key] = topic_stats

            supabase.table(TABLE_NAME).update({
                "total_marks_scored": total_marks_scored,
                "total_marks_possible": total_marks_possible,
                "previous_accuracy": prev_accuracy,
                "accuracy": new_accuracy,
                "progress_history": progress_history,
                "topics": topics,
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "updated_at": _now_iso(),
            }).eq("user_id", user_id).eq("study_space_id", study_space_id).eq("subject", subject).execute()

            # 1. Fetch full updated analytics row
            updated_row_resp = (
                supabase.table(TABLE_NAME)
                .select("*")
                .eq("user_id", user_id)
                .eq("study_space_id", study_space_id)
                .eq("subject", subject)
                .single()
                .execute()
            )
            updated_row = updated_row_resp.data

            # 2. Log analytics history
            log_analytics_history(
                analytics_row=updated_row,
                attempt={
                    "topic": topic,
                    "marks_scored": marks_scored,
                    "marks_possible": marks_possible,
                    "recent_accuracy": recent_accuracy,
                    "new_accuracy": new_accuracy,
                }
            )


        else:
            total_marks_scored = marks_scored
            total_marks_possible = marks_possible
            new_accuracy = ALPHA * recent_accuracy + (1 - ALPHA) * 0

            progress_history = [{
                "timestamp": _now_iso(),
                "topic": topic,
                "recent_accuracy": recent_accuracy,
                "previous_accuracy": 0,
                "new_accuracy": new_accuracy,
                "marks_scored": marks_scored,
                "marks_possible": marks_possible,
            }]

            topic_stats = {
                "total_questions": 1,
                "correct_answers": 1 if marks_possible > 0 and abs(marks_scored - marks_possible) < 1e-6 else 0,
                "total_marks_scored": marks_scored,
                "total_marks_possible": marks_possible,
                "accuracy": ALPHA * recent_accuracy + (1 - ALPHA) * 0,
            }

            topics = {topic or "general": topic_stats}

            supabase.table(TABLE_NAME).insert({
                "user_id": user_id,
                "study_space_id": study_space_id,
                "subject": subject,
                "total_marks_scored": total_marks_scored,
                "total_marks_possible": total_marks_possible,
                "previous_accuracy": 0,
                "accuracy": new_accuracy,
                "progress_history": progress_history,
                "topics": topics,
                "total_questions": 1,
                "correct_answers": 1 if marks_scored == marks_possible else 0,
                "updated_at": _now_iso(),
            }).execute()

            # 1. Fetch the newly-created analytics row
            updated_row_resp = (
                supabase.table(TABLE_NAME)
                .select("*")
                .eq("user_id", user_id)
                .eq("study_space_id", study_space_id)
                .eq("subject", subject)
                .single()
                .execute()
            )
            updated_row = updated_row_resp.data

            # 2. Log history
            log_analytics_history(
                analytics_row=updated_row,
                attempt={
                    "topic": topic,
                    "marks_scored": marks_scored,
                    "marks_possible": marks_possible,
                    "recent_accuracy": recent_accuracy,
                    "new_accuracy": new_accuracy,
                }
            )


        logging.debug(f"[ANALYTICS UPDATED] {user_id} | {subject} | {topic} | {marks_scored}/{marks_possible}")
        return {
            "user_id": user_id,
            "study_space_id": study_space_id,
            "subject": subject,
            "topic": topic,
            "recent_accuracy": recent_accuracy,
            "accuracy": new_accuracy,
        }

    except Exception as e:
        logging.error(f"[SUPABASE ANALYTICS ERROR] {e}")
        raise e


def _make_feedback_entry(
    comment: str,
    weak_topic: bool,
    marks_scored: float,
    marks_possible: float,
) -> Dict[str, Any]:
    return {
        "timestamp": _now_iso(),
        "comment": comment,
        "weak_topic": weak_topic,
        "marks_scored": marks_scored,
        "marks_possible": marks_possible,
    }


def _build_feedback_summary_from_entries(entries: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    strengths: List[str] = []
    needs_attention: List[str] = []

    if not entries:
        return {"strengths": strengths, "needs_attention": needs_attention}

    total_scored = sum(e.get("marks_scored", 0) for e in entries)
    total_possible = sum(e.get("marks_possible", 0) for e in entries) or 1
    # using weighted accuracy on feedback entries
    prev = 0
    for e in entries:
        entry_acc = (e["marks_scored"] / e["marks_possible"]) * 100 if e["marks_possible"] > 0 else 0
        prev = ALPHA * entry_acc + (1 - ALPHA) * prev
    avg_accuracy = prev


    weak_count = sum(1 for e in entries if e.get("weak_topic"))

    # Static logic removed.  
    # Fallback only -> return empty lists.
    return {"strengths": [], "needs_attention": []}



def update_feedback_analytics(
    user_id: str,
    study_space_id: str,
    subject: str,
    topic: str,
    comment: str,
    weak_topic: bool,
    marks_scored: float,
    marks_possible: float,
):

    resp = (
        supabase.table(TABLE_NAME)
        .select("*")
        .eq("user_id", user_id)
        .eq("study_space_id", study_space_id)
        .eq("subject", subject)
        .execute()
    )
    if len(resp.data) > 1:
        raise RuntimeError(
            f"DATA INTEGRITY ERROR: Duplicate analytics rows detected for user={user_id}, space={study_space_id}, subject={subject}"
        )


    if not resp.data:
        feedback_entry = _make_feedback_entry(comment, weak_topic, marks_scored, marks_possible)
        feedback_history_all = {topic: [feedback_entry]}
        feedback_count_all = {topic: 1}
        feedback_summary_all = {
            topic: generate_topic_feedback_summary(
                topic=topic,
                topic_stats={},
                last_n_feedback=[feedback_entry],
                previous_summary={"strengths": [], "needs_attention": []}
            )
        }


        supabase.table(TABLE_NAME).insert({
            "user_id": user_id,
            "study_space_id": study_space_id,
            "subject": subject,
            "feedback_history": feedback_history_all,
            "feedback_count": feedback_count_all,
            "feedback_summary": feedback_summary_all,
            "updated_at": _now_iso(),
        }).execute()
        return feedback_summary_all[topic]

    existing = resp.data[0]

    feedback_history_all = existing.get("feedback_history") or {}
    if not isinstance(feedback_history_all, dict):
        feedback_history_all = {}

    feedback_summary_all = existing.get("feedback_summary") or {}
    if not isinstance(feedback_summary_all, dict):
        feedback_summary_all = {}

    feedback_count_all = existing.get("feedback_count") or {}
    if not isinstance(feedback_count_all, dict):
        feedback_count_all = {}

    # load topics and topic_node for contextual LLM input
    topics = existing.get("topics") or {}
    if not isinstance(topics, dict):
        topics = {}
    topic_key = topic or "general"

    topic_feedback_history = feedback_history_all.get(topic_key) or []
    topic_feedback_count = feedback_count_all.get(topic_key) or 0
    topic_feedback_summary = feedback_summary_all.get(topic_key) or {
        "strengths": [],
        "needs_attention": []
    }

    feedback_entry = _make_feedback_entry(comment, weak_topic, marks_scored, marks_possible)

    topic_feedback_history.append(feedback_entry)
    if len(topic_feedback_history) > MAX_FEEDBACK_HISTORY:
        topic_feedback_history = topic_feedback_history[-MAX_FEEDBACK_HISTORY:]

    topic_feedback_count += 1

    if topic_feedback_count % FEEDBACK_SUMMARY_FREQUENCY == 0:
        last_n_topic = topic_feedback_history[-FEEDBACK_SUMMARY_FREQUENCY:]

        previous_summary = topic_feedback_summary or {
            "strengths": [],
            "needs_attention": []
        }

        # topics (topic stats) are passed as context but we never write feedback into topics
        topic_feedback_summary = generate_topic_feedback_summary(
            topic=topic_key,
            topic_stats=topics.get(topic_key, {
                "accuracy": 0,
                "total_questions": 0,
                "total_marks_scored": 0,
                "total_marks_possible": 0,
                "correct_answers": 0
            }),

            last_n_feedback=last_n_topic,
            previous_summary=previous_summary
        )


    feedback_history_all[topic_key] = topic_feedback_history
    feedback_count_all[topic_key] = topic_feedback_count
    feedback_summary_all[topic_key] = topic_feedback_summary

    supabase.table(TABLE_NAME).update({
        "feedback_history": feedback_history_all,
        "feedback_count": feedback_count_all,
        "feedback_summary": feedback_summary_all,
        "updated_at": _now_iso(),
    }).eq("id", existing["id"]).execute()

    # 1. Fetch updated analytics row
    updated_row_resp = (
        supabase.table(TABLE_NAME)
        .select("*")
        .eq("id", existing["id"])
        .single()
        .execute()
    )
    updated_row = updated_row_resp.data

    # 2. Log the history update for feedback
    log_analytics_history(
        analytics_row=updated_row,
        attempt={
            "topic": topic,
            "marks_scored": marks_scored,
            "marks_possible": marks_possible,
            "recent_accuracy": 0,     # feedback does not change recent acc
            "new_accuracy": 0,
        }
    )


    logging.debug(
        f"[FEEDBACK UPDATED] {user_id} | {subject} | topic={topic_key} | count={topic_feedback_count}"
    )

    return topic_feedback_summary
