from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.schemas import CreateUserRequest, QueueResponse, UpdateUserRequest, UserView
from src.services.aqis_service import (
    QueueEmptyError,
    UserAlreadyExistsError,
    UserNotFoundError,
    aqis_service,
)


def add_user(db: Session, payload: CreateUserRequest) -> UserView:
    try:
        return aqis_service.add_user(db, payload)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


def update_user(db: Session, user_id: str, payload: UpdateUserRequest) -> UserView:
    try:
        return aqis_service.update_user(db, user_id, payload)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def get_queue(db: Session) -> QueueResponse:
    return QueueResponse(users=aqis_service.get_queue_ordered(db))


def get_next_user(db: Session) -> UserView:
    try:
        return aqis_service.extract_next(db)
    except QueueEmptyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
