from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class MentoringReview(Base):
    __tablename__ = "mentoring_reviews"
    __table_args__ = (UniqueConstraint("match_id", name="uq_review_match"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("mentoring_matches.id"),
        nullable=False,
        index=True,
    )
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    mentee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    match = relationship("MentoringMatch", back_populates="review")
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="reviews_received")
    mentee = relationship("User", foreign_keys=[mentee_id], back_populates="reviews_written")
