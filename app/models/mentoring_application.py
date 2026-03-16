from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class MentoringApplication(Base):
    __tablename__ = "mentoring_applications"
    __table_args__ = (UniqueConstraint("post_id", "mentor_id", name="uq_post_mentor"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("mentoring_posts.id"),
        nullable=False,
        index=True,
    )
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    post = relationship("MentoringPost", back_populates="applications")
    mentor = relationship("User", back_populates="applications")
