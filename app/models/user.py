from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    introduction: Mapped[str | None] = mapped_column(String(500), nullable=True)
    major: Mapped[str] = mapped_column(String(100), nullable=False)
    tech_stack: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_image: Mapped[str | None] = mapped_column(String(255), nullable=True)

    posts = relationship("MentoringPost", back_populates="author", cascade="all, delete-orphan")
    applications = relationship(
        "MentoringApplication",
        back_populates="mentor",
        cascade="all, delete-orphan",
    )
    social_accounts = relationship(
        "SocialAccount",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    mentoring_matches = relationship(
        "MentoringMatch",
        foreign_keys="MentoringMatch.mentor_id",
        back_populates="mentor",
        cascade="all, delete-orphan",
    )
    selected_matches = relationship(
        "MentoringMatch",
        foreign_keys="MentoringMatch.selected_by_id",
        back_populates="selected_by",
        cascade="all, delete-orphan",
    )
    reviews_received = relationship(
        "MentoringReview",
        foreign_keys="MentoringReview.mentor_id",
        back_populates="mentor",
        cascade="all, delete-orphan",
    )
    reviews_written = relationship(
        "MentoringReview",
        foreign_keys="MentoringReview.mentee_id",
        back_populates="mentee",
        cascade="all, delete-orphan",
    )
