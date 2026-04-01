# Little-BE API Contract (Web/Mobile)

## Auth

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
