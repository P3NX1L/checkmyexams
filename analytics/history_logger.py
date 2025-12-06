from app.analytics_history.builder import build_history_rows
from app.analytics_history.repository import save_history_event

def log_analytics_history(analytics_row: dict, attempt: dict):
    main, topics, progress, feedback, summary = build_history_rows(
        analytics_row=analytics_row,
        attempt=attempt
    )
    save_history_event(main, topics, progress, feedback, summary)
