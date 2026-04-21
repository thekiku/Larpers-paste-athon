from __future__ import annotations

import heapq
import time
from threading import Lock

from sqlalchemy.orm import Session

from src.config.settings import SCORING_CONFIG
from src.models.db_user import ActiveUser
from src.models.queue_entry import QueueEntry
from src.models.schemas import CreateUserRequest, UpdateUserRequest, UserView
from src.utils.heap import HeapItem, MaxHeap


class QueueError(Exception):
    pass


class UserAlreadyExistsError(QueueError):
    pass


class UserNotFoundError(QueueError):
    pass


class QueueEmptyError(QueueError):
    pass


class AQISService:
    def __init__(self) -> None:
        self.heap = MaxHeap()
        self.latest_version: dict[str, int] = {}
        self.active_users: dict[str, QueueEntry] = {}
        self._sequence = 0
        self._lock = Lock()

    @staticmethod
    def _to_user_view(entry: QueueEntry) -> UserView:
        return UserView(
            user_id=entry.user_id,
            user_name=entry.user_name,
            urgency=entry.urgency,
            category_weight=entry.category_weight,
            arrival_time_ms=entry.arrival_time_ms,
            version=entry.version,
            score=entry.score,
        )

    def bootstrap_from_db(self, db: Session) -> None:
        with self._lock:
            self.heap = MaxHeap()
            self.latest_version = {}
            self.active_users = {}
            self._sequence = 0

            rows = db.query(ActiveUser).all()
            for row in rows:
                entry = QueueEntry(
                    user_id=row.user_id,
                    user_name=row.user_name,
                    urgency=row.urgency,
                    category_weight=row.category_weight,
                    arrival_time_ms=row.arrival_time_ms,
                    version=row.version,
                    score=row.score,
                )
                self.latest_version[row.user_id] = row.version
                self.active_users[row.user_id] = entry
                self._sequence += 1
                self.heap.push(entry, self._sequence)

    def _ensure_loaded(self, db: Session) -> None:
        # If process memory was reset but DB still has active users, rebuild heap/maps.
        if self.active_users:
            return
        has_rows = db.query(ActiveUser.user_id).first() is not None
        if has_rows:
            self.bootstrap_from_db(db)

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _compute_score(urgency: float, category_weight: float, arrival_time_ms: int) -> float:
        cfg = SCORING_CONFIG
        return (cfg.alpha * urgency) + (cfg.gamma * category_weight) - (cfg.beta * arrival_time_ms)

    def _is_entry_valid(self, entry: QueueEntry) -> bool:
        current_version = self.latest_version.get(entry.user_id)
        if current_version is None:
            return False
        active_entry = self.active_users.get(entry.user_id)
        if active_entry is None:
            return False
        return current_version == entry.version and active_entry.version == entry.version

    def add_user(self, db: Session, payload: CreateUserRequest) -> UserView:
        with self._lock:
            self._ensure_loaded(db)
            existing = db.get(ActiveUser, payload.user_id)
            if existing is not None:
                raise UserAlreadyExistsError(f"User '{payload.user_id}' already exists")

            arrival_time_ms = self._now_ms()
            version = 1
            score = self._compute_score(payload.urgency, payload.category_weight, arrival_time_ms)
            user_name = payload.user_name.strip() if payload.user_name else payload.user_id

            entry = QueueEntry(
                user_id=payload.user_id,
                user_name=user_name,
                urgency=payload.urgency,
                category_weight=payload.category_weight,
                arrival_time_ms=arrival_time_ms,
                version=version,
                score=score,
            )

            self.latest_version[payload.user_id] = version
            self.active_users[payload.user_id] = entry
            self._sequence += 1
            self.heap.push(entry, self._sequence)

            db.add(
                ActiveUser(
                    user_id=entry.user_id,
                    user_name=entry.user_name,
                    urgency=entry.urgency,
                    category_weight=entry.category_weight,
                    arrival_time_ms=entry.arrival_time_ms,
                    version=entry.version,
                    score=entry.score,
                )
            )
            db.commit()
            return self._to_user_view(entry)

    def update_user(self, db: Session, user_id: str, payload: UpdateUserRequest) -> UserView:
        with self._lock:
            self._ensure_loaded(db)
            db_user = db.get(ActiveUser, user_id)
            if db_user is None:
                raise UserNotFoundError(f"User '{user_id}' not found")

            current = self.active_users.get(user_id)
            if current is None:
                current = QueueEntry(
                    user_id=db_user.user_id,
                    user_name=db_user.user_name,
                    urgency=db_user.urgency,
                    category_weight=db_user.category_weight,
                    arrival_time_ms=db_user.arrival_time_ms,
                    version=db_user.version,
                    score=db_user.score,
                )
                self.latest_version[user_id] = current.version
                self.active_users[user_id] = current

            urgency = payload.urgency if payload.urgency is not None else current.urgency
            category_weight = (
                payload.category_weight if payload.category_weight is not None else current.category_weight
            )
            user_name = payload.user_name.strip() if payload.user_name is not None else current.user_name
            version = self.latest_version[user_id] + 1
            score = self._compute_score(urgency, category_weight, current.arrival_time_ms)

            # Lazy update: push a new version into the heap and keep old versions as stale.
            entry = QueueEntry(
                user_id=user_id,
                user_name=user_name,
                urgency=urgency,
                category_weight=category_weight,
                arrival_time_ms=current.arrival_time_ms,
                version=version,
                score=score,
            )

            self.latest_version[user_id] = version
            self.active_users[user_id] = entry
            self._sequence += 1
            self.heap.push(entry, self._sequence)

            db_user.user_name = entry.user_name
            db_user.urgency = entry.urgency
            db_user.category_weight = entry.category_weight
            db_user.arrival_time_ms = entry.arrival_time_ms
            db_user.version = entry.version
            db_user.score = entry.score
            db.commit()
            return self._to_user_view(entry)

    def extract_next(self, db: Session) -> UserView:
        with self._lock:
            self._ensure_loaded(db)
            while len(self.heap) > 0:
                entry = self.heap.pop()
                if not self._is_entry_valid(entry):
                    continue

                # Removing from active maps makes all remaining older entries stale.
                self.latest_version.pop(entry.user_id, None)
                self.active_users.pop(entry.user_id, None)
                db_user = db.get(ActiveUser, entry.user_id)
                if db_user is not None:
                    db.delete(db_user)
                    db.commit()
                return self._to_user_view(entry)

            raise QueueEmptyError("Queue is empty")

    def get_queue_ordered(self, db: Session) -> list[UserView]:
        with self._lock:
            self._ensure_loaded(db)
            rows = (
                db.query(ActiveUser)
                .order_by(ActiveUser.score.desc(), ActiveUser.arrival_time_ms.asc())
                .all()
            )
            return [
                UserView(
                    user_id=row.user_id,
                    user_name=row.user_name,
                    urgency=row.urgency,
                    category_weight=row.category_weight,
                    arrival_time_ms=row.arrival_time_ms,
                    version=row.version,
                    score=row.score,
                )
                for row in rows
            ]


aqis_service = AQISService()
