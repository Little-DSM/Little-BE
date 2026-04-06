from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class MentoringMatch(Base):
    __tablename__ = "mentoring_matches"
    __table_args__ = (UniqueConstraint("post_id", name="uq_match_post"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("mentoring_posts.id"),
        nullable=False,
        index=True,
    )
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    selected_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    selected_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    post = relationship("MentoringPost", back_populates="match")
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="mentoring_matches")
    selected_by = relationship(
        "User",
        foreign_keys=[selected_by_id],
        back_populates="selected_matches",
    )
    review = relationship(
        "MentoringReview",
        back_populates="match",
        uselist=False,
        cascade="all, delete-orphan",
    )
