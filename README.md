# Little-BE

## Prerequisites

- Python 3.11+

## Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Run the development server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Google OAuth setup

Set environment variables before running server:

```bash
export GOOGLE_CLIENT_ID="your-google-client-id"
export GOOGLE_CLIENT_SECRET="your-google-client-secret"
export GOOGLE_REDIRECT_URI="http://127.0.0.1:8000/auth/google/callback"
export GOOGLE_FRONTEND_REDIRECT_URI="http://127.0.0.1:3000/oauth/callback"
```

Google OAuth endpoints:

- `GET /auth/google/login`
- `POST /auth/google/callback`
- `POST /auth/google/token`

## Run tests

```bash
pytest
```

## Lint

```bash
ruff check .
```
