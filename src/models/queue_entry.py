from dataclasses import dataclass


@dataclass(slots=True)
class QueueEntry:
    user_id: str
    user_name: str
    urgency: float
    category_weight: float
    arrival_time_ms: int
    version: int
    score: float
