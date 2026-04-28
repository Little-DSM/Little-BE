# Little-BE API Contract (Web/Mobile)

## Auth

### GET `/auth/google/login`
- Query (optional)
  - `frontend_redirect_uri`: 로그인 완료 후 이동할 프론트 URL
- Response
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "jwt-oauth-state"
}
```

### GET `/auth/google/callback`
- Query
  - `code`
  - `state`
- Response
  - `302 Redirect` to frontend `/main`
  - query: `access_token`, `refresh_token`, `token_type`

### POST `/auth/google/token`
- Request
```json
{
  "id_token": "google-id-token"
}
```
- Response
```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "bearer"
}
```

### POST `/auth/refresh`
- Request
```json
{
  "refresh_token": "jwt-refresh-token"
}
```
- Response
```json
{
  "access_token": "new-jwt-access-token",
  "refresh_token": "new-jwt-refresh-token",
  "token_type": "bearer"
}
```

### POST `/auth/logout`
- Header: `Authorization: Bearer <access_token>`
- Request
```json
{
  "refresh_token": "jwt-refresh-token"
}
```
- Response
```json
{
  "message": "로그아웃되었습니다"
}
```

## Mentoring Post

### POST `/posts`
- Header: `Authorization: Bearer <access_token>`
- Request
```json
{
  "title": "백엔드 멘토링 필요",
  "description": "JWT, OAuth 구조",
  "major": "컴퓨터공학"
}
```

### GET `/posts`
- Header: `Authorization: Bearer <access_token>`
- Query
  - `keyword` (optional): 제목/설명/전공 통합 검색
  - `major` (optional): 전공 정확 일치

### GET `/posts/{post_id}`
- Header: `Authorization: Bearer <access_token>`

### PATCH `/posts/{post_id}`
- Header: `Authorization: Bearer <access_token>`
- 작성자만 수정 가능

### DELETE `/posts/{post_id}`
- Header: `Authorization: Bearer <access_token>`
- 작성자만 삭제 가능

### GET `/posts/{post_id}/applications`
- Header: `Authorization: Bearer <access_token>`
- 작성자만 조회 가능

## Mentor

### GET `/mentors/{mentor_id}`
- Header: `Authorization: Bearer <access_token>`
- 멘토 상세 + `application_count` 반환

## My Page

### GET `/me/posts`
- Header: `Authorization: Bearer <access_token>`
- 로그인한 사용자가 작성한 게시글 목록 조회
- Response
```json
{
  "total_count": 2,
  "items": [
    {
      "post_id": 12,
      "title": "리액트에 대해 알려주세요!",
      "image_url": "https://example.com/images/react-post.png",
      "major": "Frontend",
      "author_name": "오찬영",
      "created_at": "2026-04-28T11:00:00",
      "view_count": 0
    }
  ]
}
```
