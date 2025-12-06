from app.supabase.client import supabase

def save_history_event(main, topics, progress, feedback, summary):

    # Insert main event
    resp = supabase.table("analytics_history").insert({
        "analytics_id": main.analytics_id,
        "user_id": main.user_id,
        "study_space_id": main.study_space_id,
        "subject": main.subject,
        "topic": main.topic,
        "marks_scored": main.marks_scored,
        "marks_possible": main.marks_possible,
        "total_questions": main.total_questions,
        "correct_answers": main.correct_answers,
        "total_marks_scored": main.total_marks_scored,
        "total_marks_possible": main.total_marks_possible,
        "previous_accuracy": main.previous_accuracy,
        "accuracy": main.accuracy,
        "updated_at": main.updated_at.isoformat()
    }).execute()

    history_event_id = resp.data[0]["id"]

    # Insert topics
    for t in topics:
        supabase.table("analytics_history_topics").insert({
            "history_event_id": history_event_id,
            "topic_name": t.topic_name,
            "total_questions": t.total_questions,
            "correct_answers": t.correct_answers,
            "total_marks_scored": t.total_marks_scored,
            "total_marks_possible": t.total_marks_possible,
            "accuracy": t.accuracy
        }).execute()

    # Insert progress
    supabase.table("analytics_history_progress").insert({
        "history_event_id": history_event_id,
        "timestamp": progress.timestamp,
        "recent_accuracy": progress.recent_accuracy,
        "previous_accuracy": progress.previous_accuracy,
        "new_accuracy": progress.new_accuracy,
        "marks_scored": progress.marks_scored,
        "marks_possible": progress.marks_possible
    }).execute()

    # Insert feedback
    for fb in feedback:
        supabase.table("analytics_history_feedback").insert({
            "history_event_id": history_event_id,
            "topic_name": fb.topic_name,
            "comment": fb.comment,
            "weak_topic": fb.weak_topic,
            "marks_scored": fb.marks_scored,
            "marks_possible": fb.marks_possible,
            "timestamp": fb.timestamp
        }).execute()

    # Insert summary
    for s in summary:
        supabase.table("analytics_history_feedback_summary").insert({
            "history_event_id": history_event_id,
            "topic_name": s.topic_name,
            "strengths": s.strengths,
            "needs_attention": s.needs_attention
        }).execute()
