from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class MentoringPost(Base):
    __tablename__ = "mentoring_posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    major: Mapped[str] = mapped_column(String(100), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    author = relationship("User", back_populates="posts")
    applications = relationship(
        "MentoringApplication",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    match = relationship(
        "MentoringMatch",
        back_populates="post",
        uselist=False,
        cascade="all, delete-orphan",
    )
