from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.database.session import Base, engine
from app.models import MentoringApplication, MentoringPost, User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_user_email_column()
    _ensure_user_contact_column()
    _ensure_user_introduction_column()
    _ensure_post_image_column()

    with Session(engine) as session:
        if session.execute(select(User.id)).first():
            return

        mentee = User(
            name="김멘티",
            email="mentee@example.com",
            contact="010-1111-1111",
            introduction="백엔드 실무 역량을 키우고 싶은 멘티입니다.",
            major="컴퓨터공학",
            tech_stack="Python, FastAPI",
            profile_image="https://example.com/images/mentee.png",
        )
        mentor_a = User(
            name="박멘토",
            email="mentor-a@example.com",
            contact="010-2222-2222",
            introduction="웹 백엔드 아키텍처와 코드 리뷰 멘토링을 진행합니다.",
            major="소프트웨어공학",
            tech_stack="Python, Django, FastAPI",
            profile_image="https://example.com/images/mentor-a.png",
        )
        mentor_b = User(
            name="이멘토",
            email="mentor-b@example.com",
            contact="010-3333-3333",
            introduction="AI 모델링과 실습 중심 멘토링을 진행합니다.",
            major="인공지능",
            tech_stack="PyTorch, TensorFlow",
            profile_image="https://example.com/images/mentor-b.png",
        )
        session.add_all([mentee, mentor_a, mentor_b])
        session.flush()

        post = MentoringPost(
            title="백엔드 멘토링이 필요해요",
            image_url="https://example.com/images/post-sample.png",
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


def _ensure_user_contact_column() -> None:
    inspector = inspect(engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "contact" in user_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN contact VARCHAR(100)"))


def _ensure_user_email_column() -> None:
    inspector = inspect(engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "email" in user_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))


def _ensure_user_introduction_column() -> None:
    inspector = inspect(engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "introduction" in user_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN introduction VARCHAR(500)"))


def _ensure_post_image_column() -> None:
    inspector = inspect(engine)
    columns = inspector.get_columns("mentoring_posts")
    post_columns = {column["name"] for column in columns}
    if "image_url" not in post_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE mentoring_posts ADD COLUMN image_url TEXT"))
        return

    image_url_column = next(
        (column for column in columns if column["name"] == "image_url"),
        None,
    )
    column_type = str(image_url_column["type"]).lower() if image_url_column else ""
    if "text" in column_type:
        return

    if engine.dialect.name != "mysql":
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE mentoring_posts MODIFY COLUMN image_url TEXT"))
