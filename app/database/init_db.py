from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import Base, engine
from app.models import MentoringApplication, MentoringPost, User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        if session.execute(select(User.id)).first():
            return

        mentee = User(
            name="김멘티",
            major="컴퓨터공학",
            tech_stack="Python, FastAPI",
            profile_image="https://example.com/images/mentee.png",
        )
        mentor_a = User(
            name="박멘토",
            major="소프트웨어공학",
            tech_stack="Python, Django, FastAPI",
            profile_image="https://example.com/images/mentor-a.png",
        )
        mentor_b = User(
            name="이멘토",
            major="인공지능",
            tech_stack="PyTorch, TensorFlow",
            profile_image="https://example.com/images/mentor-b.png",
        )
        session.add_all([mentee, mentor_a, mentor_b])
        session.flush()

        post = MentoringPost(
            title="백엔드 멘토링이 필요해요",
            description="FastAPI 프로젝트 구조와 인증 설계를 배우고 싶습니다.",
            major="컴퓨터공학",
            author_id=mentee.id,
        )
        session.add(post)
        session.flush()

        session.add_all(
            [
                MentoringApplication(post_id=post.id, mentor_id=mentor_a.id),
                MentoringApplication(post_id=post.id, mentor_id=mentor_b.id),
            ]
        )
        session.commit()
