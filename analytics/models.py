from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any

class ProgressPoint(BaseModel):
    timestamp: datetime
    recent_accuracy: float
    previous_accuracy: float
    new_accuracy: float
    marks_scored: float
    marks_possible: float

class TopicStats(BaseModel):
    total_questions: int = 0
    correct_answers: int = 0
    total_marks_scored: float = 0.0
    total_marks_possible: float = 0.0
    accuracy: float = 0.0

class SubjectAnalytics(BaseModel):
    user_id: str
    study_space_id: str
    subject: str
    accuracy: float = 0.0
    total_marks_scored: float = 0.0
    total_marks_possible: float = 0.0
    previous_accuracy: float = 0.0
    progress_history: List[ProgressPoint] = Field(default_factory=list)
    topics: Dict[str, TopicStats] = Field(default_factory=dict)
    feedback_history: List[Dict[str, Any]] = Field(default_factory=list)
    feedback_summary: Dict[str, List[str]] = Field(
        default_factory=lambda: {"strengths": [], "needs_attention": []}
    )
    feedback_count: int = 0
    updated_at: datetime
