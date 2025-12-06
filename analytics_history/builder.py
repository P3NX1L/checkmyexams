from .types import (
    AnalyticsHistoryRow,
    TopicHistoryRow,
    ProgressHistoryRow,
    FeedbackHistoryRow,
    FeedbackSummaryRow
)
from datetime import datetime,timezone

def build_history_rows(analytics_row: dict, attempt: dict):
    """
    attempt = {
      "topic": "...",
      "marks_scored": x,
      "marks_possible": y,
      "recent_accuracy": z,
      "new_accuracy": a
    }
    """

    # 1) MAIN ROW
    main = AnalyticsHistoryRow(
        analytics_id=analytics_row["id"],
        user_id=analytics_row["user_id"],
        study_space_id=analytics_row["study_space_id"],
        subject=analytics_row["subject"],
        topic=attempt.get("topic"),
        marks_scored=attempt.get("marks_scored"),
        marks_possible=attempt.get("marks_possible"),
        total_questions=analytics_row["total_questions"],
        correct_answers=analytics_row["correct_answers"],
        total_marks_scored=analytics_row["total_marks_scored"],
        total_marks_possible=analytics_row["total_marks_possible"],
        previous_accuracy=analytics_row["previous_accuracy"],
        accuracy=analytics_row["accuracy"],
        updated_at=datetime.now(timezone.utc)
    )

    # 2) TOPICS
    topics = []
    for name, data in analytics_row.get("topics", {}).items():
        topics.append(TopicHistoryRow(
            topic_name=name,
            total_questions=data.get("total_questions", 0),
            correct_answers=data.get("correct_answers", 0),
            total_marks_scored=data.get("total_marks_scored", 0.0),
            total_marks_possible=data.get("total_marks_possible", 0.0),
            accuracy=data.get("accuracy", 0.0)
        ))

    # 3) LAST PROGRESS ENTRY
    last = analytics_row["progress_history"][-1]
    progress = ProgressHistoryRow(
        timestamp=last["timestamp"],
        recent_accuracy=last["recent_accuracy"],
        previous_accuracy=last["previous_accuracy"],
        new_accuracy=last["new_accuracy"],
        marks_scored=last["marks_scored"],
        marks_possible=last["marks_possible"]
    )

    # 4) FEEDBACK HISTORY
    fb_rows = []
    feedback_raw = analytics_row.get("feedback_history", {})

    # If feedback_history is a list, treat as empty dict
    if isinstance(feedback_raw, list):
        feedback_raw = {}

    for topic_name, items in feedback_raw.items():

        for fb in items:
            fb_rows.append(FeedbackHistoryRow(
                topic_name=topic_name,
                comment=fb["comment"],
                weak_topic=fb["weak_topic"],
                marks_scored=fb["marks_scored"],
                marks_possible=fb["marks_possible"],
                timestamp=fb["timestamp"]
            ))

    # 5) FEEDBACK SUMMARY
    summary_rows = []
    summary_raw = analytics_row.get("feedback_summary", {})

    # If summary is a list, replace with empty dict
    if isinstance(summary_raw, list):
        summary_raw = {}

    # Ensure each value is a dict with expected keys
    for topic_name, data in summary_raw.items():
        if not isinstance(data, dict):
            continue  # skip if malformed

        summary_rows.append(FeedbackSummaryRow(
            topic_name=topic_name,
            strengths=data.get("strengths", []),
            needs_attention=data.get("needs_attention", [])
        ))


    return main, topics, progress, fb_rows, summary_rows
