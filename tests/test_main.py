from fastapi.testclient import TestClient

from app.main import app


def get_token(client: TestClient, user_id: int = 1) -> str:
    response = client.post("/auth/login", json={"user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_auth_is_required() -> None:
    with TestClient(app) as client:
        response = client.get("/posts")

    assert response.status_code == 401
    assert response.json() == {"detail": "인증이 필요합니다"}


def test_create_and_get_post() -> None:
    with TestClient(app) as client:
        token = get_token(client, user_id=1)
        headers = {"Authorization": f"Bearer {token}"}

        create_response = client.post(
            "/posts",
            json={
                "title": "백엔드 코드 리뷰가 필요합니다",
                "description": "SQLAlchemy 구조 피드백을 받고 싶어요.",
                "major": "컴퓨터공학",
            },
            headers=headers,
        )

        assert create_response.status_code == 201
        post_id = create_response.json()["id"]

        detail_response = client.get(f"/posts/{post_id}", headers=headers)

    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "백엔드 코드 리뷰가 필요합니다"
    assert detail_response.json()["author"]["name"] == "김멘티"


def test_create_post_requires_title() -> None:
    with TestClient(app) as client:
        token = get_token(client, user_id=1)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/posts",
            json={"title": "   ", "description": "설명", "major": "컴퓨터공학"},
            headers=headers,
        )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Value error, 제목을 입력해주세요"


def test_only_author_can_update_post() -> None:
    with TestClient(app) as client:
        token = get_token(client, user_id=2)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.patch(
            "/posts/1",
            json={"title": "수정", "description": "수정", "major": "컴퓨터공학"},
            headers=headers,
        )

    assert response.status_code == 403
    assert response.json() == {"detail": "게시글 작성자만 수정 또는 삭제할 수 있습니다"}


def test_author_can_get_applications() -> None:
    with TestClient(app) as client:
        token = get_token(client, user_id=1)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/posts/1/applications", headers=headers)

    assert response.status_code == 200
    assert len(response.json()["mentors"]) == 2
