from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.controllers.queue_controller import add_user, get_next_user, get_queue, update_user
from src.db.database import get_db
from src.models.schemas import CreateUserRequest, QueueResponse, UpdateUserRequest, UserView

router = APIRouter(tags=["AQIS"])


@router.post("/user", response_model=UserView, status_code=status.HTTP_201_CREATED)
def create_user(payload: CreateUserRequest, db: Session = Depends(get_db)) -> UserView:
    return add_user(db, payload)


@router.put("/user/{user_id}", response_model=UserView)
def modify_user(user_id: str, payload: UpdateUserRequest, db: Session = Depends(get_db)) -> UserView:
    return update_user(db, user_id, payload)


@router.get("/queue", response_model=QueueResponse)
def read_queue(db: Session = Depends(get_db)) -> QueueResponse:
    return get_queue(db)


@router.get("/next", response_model=UserView)
def read_next(db: Session = Depends(get_db)) -> UserView:
    return get_next_user(db)
