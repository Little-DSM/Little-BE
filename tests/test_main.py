from fastapi.testclient import TestClient

from app.main import app


def get_token(client: TestClient, user_id: int = 1) -> str:
    response = client.post("/auth/login", json={"user_id": user_id})
    assert response.status_code == 200
    return response.json()["access_token"]


def get_token_pair(client: TestClient, user_id: int = 1) -> dict[str, str]:
    response = client.post("/auth/login", json={"user_id": user_id})
    assert response.status_code == 200
    body = response.json()
    return {
        "access_token": body["access_token"],
        "refresh_token": body["refresh_token"],
    }


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


def test_google_login_url_requires_settings(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")

    with TestClient(app) as client:
        response = client.get("/auth/google/login")

    assert response.status_code == 500
    assert response.json() == {"detail": "Google OAuth 설정이 누락되었습니다"}


def test_google_id_token_login_success(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "dummy-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "dummy-client-secret")

    def fake_verify(self, id_token_value: str):
        assert id_token_value == "dummy-id-token"
        return {
            "sub": "google-sub-123",
            "name": "Google Tester",
            "email": "tester@example.com",
            "picture": "https://example.com/profile.png",
        }

    monkeypatch.setattr(
        "app.services.auth_service.AuthService._verify_google_id_token",
        fake_verify,
    )

    with TestClient(app) as client:
        response = client.post("/auth/google/token", json={"id_token": "dummy-id-token"})

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_refresh_and_logout_flow() -> None:
    with TestClient(app) as client:
        token_pair = get_token_pair(client, user_id=1)

        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": token_pair["refresh_token"]},
        )
        assert refresh_response.status_code == 200
        new_pair = refresh_response.json()
        assert new_pair["access_token"]
        assert new_pair["refresh_token"]
        assert new_pair["refresh_token"] != token_pair["refresh_token"]

        headers = {"Authorization": f"Bearer {new_pair['access_token']}"}
        logout_response = client.post(
            "/auth/logout",
            json={"refresh_token": new_pair["refresh_token"]},
            headers=headers,
        )
        assert logout_response.status_code == 200

        fail_refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": new_pair["refresh_token"]},
        )
        assert fail_refresh_response.status_code == 401
        assert fail_refresh_response.json() == {"detail": "이미 로그아웃된 refresh token 입니다"}


def test_post_search() -> None:
    with TestClient(app) as client:
        token = get_token(client, user_id=1)
        headers = {"Authorization": f"Bearer {token}"}

        create_response = client.post(
            "/posts",
            json={
                "title": "React 멘토링 요청",
                "description": "프론트엔드 상태관리 고민",
                "major": "소프트웨어공학",
            },
            headers=headers,
        )
        assert create_response.status_code == 201

        search_response = client.get("/posts", params={"keyword": "React"}, headers=headers)
        assert search_response.status_code == 200
        assert any("React" in post["title"] for post in search_response.json())


def test_get_mentor_detail() -> None:
    with TestClient(app) as client:
        token = get_token(client, user_id=1)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/mentors/2", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == 2
    assert "application_count" in response.json()


def test_apply_and_select_mentor_flow() -> None:
    with TestClient(app) as client:
        mentee_pair = get_token_pair(client, user_id=1)
        mentor_pair = get_token_pair(client, user_id=2)

        mentee_headers = {"Authorization": f"Bearer {mentee_pair['access_token']}"}
        mentor_headers = {"Authorization": f"Bearer {mentor_pair['access_token']}"}

        create_post_response = client.post(
            "/posts",
            json={
                "title": "자료구조 멘토링 원해요",
                "description": "트리/그래프를 집중적으로 배우고 싶어요",
                "major": "컴퓨터공학",
            },
            headers=mentee_headers,
        )
        assert create_post_response.status_code == 201
        post_id = create_post_response.json()["id"]

        apply_response = client.post(f"/posts/{post_id}/apply", headers=mentor_headers)
        assert apply_response.status_code == 201

        select_response = client.post(
            f"/posts/{post_id}/select-mentor",
            json={"mentor_id": 2},
            headers=mentee_headers,
        )
        assert select_response.status_code == 200
        assert select_response.json()["mentor"]["id"] == 2

        selected_response = client.get(f"/posts/{post_id}/selected-mentor", headers=mentee_headers)
        assert selected_response.status_code == 200
        assert selected_response.json()["mentor"]["id"] == 2
