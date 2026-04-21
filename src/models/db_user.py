from sqlalchemy import BigInteger, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class ActiveUser(Base):
    __tablename__ = "active_users"

    user_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    user_name: Mapped[str] = mapped_column(String(120), nullable=False)
    urgency: Mapped[float] = mapped_column(Float, nullable=False)
    category_weight: Mapped[float] = mapped_column(Float, nullable=False)
    arrival_time_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
