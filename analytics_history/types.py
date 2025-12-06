from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class AnalyticsHistoryRow:
    analytics_id: str
    user_id: str
    study_space_id: str
    subject: str
    topic: Optional[str]
    marks_scored: float
    marks_possible: float
    total_questions: int
    correct_answers: int
    total_marks_scored: float
    total_marks_possible: float
    previous_accuracy: float
    accuracy: float
    updated_at: datetime

@dataclass
class TopicHistoryRow:
    topic_name: str
    total_questions: int
    correct_answers: int
    total_marks_scored: float
    total_marks_possible: float
    accuracy: float

@dataclass
class ProgressHistoryRow:
    timestamp: datetime
    recent_accuracy: float
    previous_accuracy: float
    new_accuracy: float
    marks_scored: float
    marks_possible: float

@dataclass
class FeedbackHistoryRow:
    topic_name: str
    comment: str
    weak_topic: bool
    marks_scored: float
    marks_possible: float
    timestamp: datetime

@dataclass
class FeedbackSummaryRow:
    topic_name: str
    strengths: List[str]
    needs_attention: List[str]
