from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.auth.jwt import verify_oauth_state_token
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
                "image_url": "https://example.com/images/backend-review.png",
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
    assert detail_response.json()["image_url"] == "https://example.com/images/backend-review.png"
    assert detail_response.json()["author"]["id"] == 1


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


def test_google_login_url_supports_frontend_redirect(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "dummy-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "dummy-client-secret")
    monkeypatch.setenv(
        "GOOGLE_ALLOWED_FRONTEND_REDIRECT_URIS",
        "https://little-fe.vercel.app/main,http://localhost:5173/main",
    )

    with TestClient(app) as client:
        response = client.get(
            "/auth/google/login",
            params={"frontend_redirect_uri": "http://localhost:5173/main"},
        )

    assert response.status_code == 200
    state = response.json()["state"]
    assert verify_oauth_state_token(state) == "http://localhost:5173/main"


def test_google_login_url_rejects_not_allowed_frontend_redirect(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "dummy-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "dummy-client-secret")
    monkeypatch.setenv(
        "GOOGLE_ALLOWED_FRONTEND_REDIRECT_URIS",
        "https://little-fe.vercel.app/main,http://localhost:5173/main",
    )

    with TestClient(app) as client:
        response = client.get(
            "/auth/google/login",
            params={"frontend_redirect_uri": "https://evil.example.com/main"},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "허용되지 않은 프론트엔드 리다이렉트 URI 입니다"}


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


def test_google_callback_get_redirects_to_frontend(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "dummy-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "dummy-client-secret")

    def fake_login(self, code: str, state: str):
        assert code == "dummy-code"
        assert state == "dummy-state"
        return (
            {
                "access_token": "access-token-value",
                "refresh_token": "refresh-token-value",
            },
            "https://little-fe.vercel.app/main",
        )

    monkeypatch.setattr(
        "app.services.auth_service.AuthService.login_with_google_code_for_frontend_redirect",
        fake_login,
    )

    with TestClient(app) as client:
        response = client.get(
            "/auth/google/callback",
            params={"code": "dummy-code", "state": "dummy-state"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers["location"]
    parsed = urlparse(location)
    query = parse_qs(parsed.query)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == "https://little-fe.vercel.app/main"
    assert query["access_token"] == ["access-token-value"]
    assert query["refresh_token"] == ["refresh-token-value"]
    assert query["token_type"] == ["bearer"]


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
    assert "email" in response.json()
    assert "application_count" in response.json()
    assert "rating_average" in response.json()
    assert "rating_count" in response.json()
    assert "contact" in response.json()


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


def test_my_page_get_and_update() -> None:
    with TestClient(app) as client:
        token = get_token(client, user_id=1)
        headers = {"Authorization": f"Bearer {token}"}

        get_response = client.get("/me", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["id"] == 1
        assert "email" in get_response.json()
        assert "introduction" in get_response.json()
        assert "profile_image" in get_response.json()
        assert "major" in get_response.json()
        assert "rating_average" in get_response.json()
        assert "rating_count" in get_response.json()

        update_response = client.patch(
            "/me",
            json={
                "name": "업데이트멘티",
                "introduction": "자기소개를 업데이트했습니다.",
                "profile_image": "https://example.com/images/updated-profile.png",
                "major": "소프트웨어공학",
            },
            headers=headers,
        )
        assert update_response.status_code == 200
        body = update_response.json()
        assert body["name"] == "업데이트멘티"
        assert body["introduction"] == "자기소개를 업데이트했습니다."
        assert body["profile_image"] == "https://example.com/images/updated-profile.png"
        assert body["major"] == "소프트웨어공학"


def test_rating_is_reflected_on_mentor_profile() -> None:
    with TestClient(app) as client:
        mentee_pair = get_token_pair(client, user_id=1)
        mentor_pair = get_token_pair(client, user_id=2)

        mentee_headers = {"Authorization": f"Bearer {mentee_pair['access_token']}"}
        mentor_headers = {"Authorization": f"Bearer {mentor_pair['access_token']}"}

        create_post_response = client.post(
            "/posts",
            json={
                "title": "운영체제 멘토링 받고 싶어요",
                "description": "스케줄링과 동기화 개념을 배우고 싶습니다.",
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

        review_response = client.post(
            f"/posts/{post_id}/review",
            json={"rating": 5, "comment": "설명이 명확하고 친절했어요."},
            headers=mentee_headers,
        )
        assert review_response.status_code == 200
        assert review_response.json()["rating"] == 5

        mentor_detail_response = client.get("/mentors/2", headers=mentee_headers)
        assert mentor_detail_response.status_code == 200
        assert mentor_detail_response.json()["rating_average"] is not None
        assert mentor_detail_response.json()["rating_count"] >= 1


def test_get_mentor_reviews_summary() -> None:
    with TestClient(app) as client:
        mentee_pair = get_token_pair(client, user_id=1)
        mentor_pair = get_token_pair(client, user_id=2)

        mentee_headers = {"Authorization": f"Bearer {mentee_pair['access_token']}"}
        mentor_headers = {"Authorization": f"Bearer {mentor_pair['access_token']}"}

        create_post_response = client.post(
            "/posts",
            json={
                "title": "자료구조 멘토링 원해요",
                "image_url": "https://example.com/images/ds-mentoring.png",
                "description": "트리와 그래프를 같이 보고 싶어요.",
                "major": "컴퓨터공학",
            },
            headers=mentee_headers,
        )
        assert create_post_response.status_code == 201
        post_id = create_post_response.json()["id"]

        assert client.post(f"/posts/{post_id}/apply", headers=mentor_headers).status_code == 201
        assert (
            client.post(
                f"/posts/{post_id}/select-mentor",
                json={"mentor_id": 2},
                headers=mentee_headers,
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/posts/{post_id}/review",
                json={"rating": 4, "comment": "꼼꼼하게 알려주셨어요."},
                headers=mentee_headers,
            ).status_code
            == 200
        )

        reviews_response = client.get("/mentors/2/reviews", headers=mentee_headers)
        assert reviews_response.status_code == 200
        body = reviews_response.json()
        assert body["mentor_id"] == 2
        assert body["total_reviews"] >= 1
        assert "distribution" in body
        assert isinstance(body["reviews"], list)
        assert body["reviews"][0]["post_title"]
        assert body["reviews"][0]["reviewer_nickname"].startswith("익명의 ")


def test_get_my_mentoring_progress_with_status_and_contact() -> None:
    with TestClient(app) as client:
        mentee_pair = get_token_pair(client, user_id=1)
        mentor_pair = get_token_pair(client, user_id=2)
        mentee_headers = {"Authorization": f"Bearer {mentee_pair['access_token']}"}
        mentor_headers = {"Authorization": f"Bearer {mentor_pair['access_token']}"}

        in_progress_post = client.post(
            "/posts",
            json={
                "title": "진행중 멘토링",
                "description": "리뷰 전 상태를 확인하려고 합니다.",
                "major": "Frontend",
            },
            headers=mentee_headers,
        )
        assert in_progress_post.status_code == 201
        in_progress_post_id = in_progress_post.json()["id"]

        assert (
            client.post(
                f"/posts/{in_progress_post_id}/apply",
                headers=mentor_headers,
            ).status_code
            == 201
        )
        assert (
            client.post(
                f"/posts/{in_progress_post_id}/select-mentor",
                json={"mentor_id": 2},
                headers=mentee_headers,
            ).status_code
            == 200
        )

        completed_post = client.post(
            "/posts",
            json={
                "title": "완료 멘토링",
                "description": "리뷰 완료 상태를 확인하려고 합니다.",
                "major": "Backend",
            },
            headers=mentee_headers,
        )
        assert completed_post.status_code == 201
        completed_post_id = completed_post.json()["id"]

        assert (
            client.post(
                f"/posts/{completed_post_id}/apply",
                headers=mentor_headers,
            ).status_code
            == 201
        )
        assert (
            client.post(
                f"/posts/{completed_post_id}/select-mentor",
                json={"mentor_id": 2},
                headers=mentee_headers,
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/posts/{completed_post_id}/review",
                json={"rating": 5, "comment": "도움이 많이 됐어요."},
                headers=mentee_headers,
            ).status_code
            == 200
        )

        all_response = client.get("/me/mentoring-progress", headers=mentee_headers)
        assert all_response.status_code == 200
        all_items = all_response.json()["items"]
        assert any(item["title"] == "진행중 멘토링" for item in all_items)
        assert any(item["title"] == "완료 멘토링" for item in all_items)
        for item in all_items:
            if item["title"] in {"진행중 멘토링", "완료 멘토링"}:
                assert item["mentor_contact"]

        in_progress_response = client.get(
            "/me/mentoring-progress",
            params={"status": "in_progress"},
            headers=mentee_headers,
        )
        assert in_progress_response.status_code == 200
        in_progress_items = in_progress_response.json()["items"]
        assert any(item["title"] == "진행중 멘토링" for item in in_progress_items)
        assert all(item["status"] == "IN_PROGRESS" for item in in_progress_items)

        completed_response = client.get(
            "/me/mentoring-progress",
            params={"status": "completed"},
            headers=mentee_headers,
        )
        assert completed_response.status_code == 200
        completed_items = completed_response.json()["items"]
        assert any(item["title"] == "완료 멘토링" for item in completed_items)
        assert all(item["status"] == "COMPLETED" for item in completed_items)


def test_get_my_posts_only_returns_current_user_posts() -> None:
    with TestClient(app) as client:
        my_token = get_token(client, user_id=1)
        my_headers = {"Authorization": f"Bearer {my_token}"}
        other_token = get_token(client, user_id=2)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        my_create_1 = client.post(
            "/posts",
            json={
                "title": "내 게시글 A",
                "image_url": "https://example.com/images/my-a.png",
                "description": "내가 작성한 첫 번째 글",
                "major": "Frontend",
            },
            headers=my_headers,
        )
        assert my_create_1.status_code == 201

        my_create_2 = client.post(
            "/posts",
            json={
                "title": "내 게시글 B",
                "image_url": "https://example.com/images/my-b.png",
                "description": "내가 작성한 두 번째 글",
                "major": "Backend",
            },
            headers=my_headers,
        )
        assert my_create_2.status_code == 201

        other_create = client.post(
            "/posts",
            json={
                "title": "다른 사람 글",
                "description": "내 글 목록에 보이면 안됨",
                "major": "AI",
            },
            headers=other_headers,
        )
        assert other_create.status_code == 201

        response = client.get("/me/posts", headers=my_headers)
        assert response.status_code == 200
        body = response.json()
        assert "total_count" in body
        assert body["total_count"] >= 2
        assert isinstance(body["items"], list)
        titles = [item["title"] for item in body["items"]]
        assert "내 게시글 A" in titles
        assert "내 게시글 B" in titles
        assert "다른 사람 글" not in titles
        assert all(item["author_name"] for item in body["items"])
