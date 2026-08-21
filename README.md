# 📄 DocFlow API

> A production-style document management API with JWT authentication, asynchronous processing, and a fully Dockerized development environment.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-Background%20Tasks-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

DocFlow is a RESTful API for securely managing user documents.Users can register, authenticate with JWT, upload files, track background processing through Celery, download their documents, and delete them when no longer needed.

---

## ✨ Why DocFlow?

This project demonstrates a practical backend architecture rather than a simple CRUD application:

- 🔐 **JWT-based authentication** with OAuth2 Password Flow
- 📤 Secure, user-specific document uploads
- ⚙️ **Asynchronous processing** using Celery workers
- 📨 Redis as the Celery broker and result backend
- 🗄️ PostgreSQL with asynchronous SQLAlchemy
- 🧬 Database schema versioning with Alembic
- 🐳 Fully containerized with Docker Compose
- 🧪 Automated test suite using Pytest
- 📚 Interactive API documentation via Swagger UI

---

## 🏗️ Architecture

```text
                    ┌──────────────────┐
                    │   Client / UI    │
                    └────────┬─────────┘
                             │ HTTP + JWT
                             ▼
┌───────────────────────────────────────────────┐
│                 FastAPI Service                │
│              http://localhost:8000             │
└───────┬───────────────────┬───────────────────┘
        │                   │
        │                   │ Sends processing task
        ▼                   ▼
┌───────────────┐    ┌───────────────┐
│  PostgreSQL   │    │ Celery Worker │
│ User & File   │    │ Background    │
│ Metadata      │    │ Processing    │
└───────────────┘    └───────┬───────┘
                             │
                             ▼
                      ┌─────────────┐
                      │    Redis    │
                      │ Broker/Store│
                      └─────────────┘
```

---

## 🧰 Tech Stack

| Area | Technology |
|---|---|
| API Framework | FastAPI |
| ASGI Server | Uvicorn |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy Async |
| Authentication | JWT + OAuth2 Password Flow |
| Background Processing | Celery |
| Broker / Result Backend | Redis 7 |
| Database Migrations | Alembic |
| Testing | Pytest |
| Containerization | Docker & Docker Compose |

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd docflow-api
```

### 2. Create the environment file

**Linux / macOS**

```bash
cp .env.example .env
```

**PowerShell**

```powershell
Copy-Item .env.example .env
```

### 3. Build and start all services

```bash
docker compose up --build -d
```

### 4. Apply database migrations

```bash
docker compose exec api alembic upgrade head
```

### 5. Open Swagger UI 🎉

Visit:

```text
http://localhost:8000/docs
```

---

## 🐳 Docker Services

The application is composed of four containers:

| Service | Container Name | Role | Exposed Port |
|---|---|---|---|
| API | `docflow-api` | FastAPI application | `8000` |
| Worker | `docflow-worker` | Celery background worker | — |
| PostgreSQL | `docflow-postgres` | Persistent database | `5433` |
| Redis | `docflow-redis` | Celery broker and result backend | `6379` |

Check that everything is running:

```bash
docker compose ps
```

Expected result: all services should be running, and PostgreSQL should report `healthy`.

---

## 🔐 Environment Variables

Create a `.env` file based on `.env.example`.

```env
# Security
SECRET_KEY=replace-with-a-long-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+asyncpg://docflow_user:docflow_password@postgres:5432/docflow_db

# Celery / Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

> [!IMPORTANT]
> `postgres` and `redis` are Docker Compose service names.> These hostnames work from inside containers. They should not be used as hostnames when connecting directly from your machine.

---

## 📁 Project Structure

```text
docflow-api/
│
├── app/
│   ├── api/                 # Authentication dependencies
│   ├── core/                # Configuration and security utilities
│   ├── workers/             # Celery configuration and tasks
│   ├── database.py          # Async database setup
│   ├── main.py              # FastAPI routes and application entry point
│   ├── models.py            # SQLAlchemy database models
│   └── schemas.py           # Pydantic request/response schemas
│
├── alembic/                 # Database migration files
├── tests/                   # Automated tests
├── uploads/                 # Uploaded files (created at runtime)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔗 API Overview

### Public Endpoints

| Method | Endpoint | Description |
|:---:|---|---|
| `GET` | `/` | Welcome endpoint |
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/token` | Login and receive JWT token |

### Protected Endpoints 🔒

All endpoints below require this header:

```http
Authorization: Bearer <access_token>
```

| Method | Endpoint | Description |
|:---:|---|---|
| `GET` | `/auth/me` | Get current authenticated user |
| `POST` | `/documents/upload` | Upload a document and trigger processing |
| `GET` | `/documents/` | List current user's documents |
| `GET` | `/documents/{document_id}` | Get document metadata |
| `GET` | `/documents/{document_id}/status` | Get stored processing status |
| `GET` | `/documents/{document_id}/task` | Get Celery task status and result |
| `GET` | `/documents/{document_id}/download` | Download the original file |
| `DELETE` | `/documents/{document_id}` | Delete a document and its physical file |

---

## 🔑 Authentication Flow

### Register a user

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "strong-password"
  }'
```

### Obtain an access token

> [!NOTE]
> The OAuth2 form expects the email address in the `username` field.

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=strong-password"
```

Example response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Store the token

**Linux / macOS**

```bash
export TOKEN="your_access_token"
```

**PowerShell**

```powershell
$TOKEN = "your_access_token"
```

---

## 📄 Document Workflow

```text
Upload file
    │
    ▼
Store file in uploads/<user_id>/
    │
    ▼
Save document metadata in PostgreSQL
    │
    ▼
Dispatch Celery task through Redis
    │
    ▼
Celery worker processes document
    │
    ▼
Check document/task status through API
```

### Upload a document

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@example.pdf"
```

### List documents

```bash
curl "http://localhost:8000/documents/?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Check processing status

```bash
curl "http://localhost:8000/documents/1/status" \
  -H "Authorization: Bearer $TOKEN"
```

### Check Celery task status

```bash
curl "http://localhost:8000/documents/1/task" \
  -H "Authorization: Bearer $TOKEN"
```

### Download a document

```bash
curl "http://localhost:8000/documents/1/download" \
  -H "Authorization: Bearer $TOKEN" \
  --output downloaded-file.pdf
```

### Delete a document

```bash
curl -X DELETE "http://localhost:8000/documents/1" \
  -H "Authorization: Bearer $TOKEN"
```

A successful deletion returns:

```text
204 No Content
```

---

## 🧬 Database Migrations

Create a migration after modifying SQLAlchemy models:

```bash
docker compose exec api alembic revision --autogenerate -m "describe your change"
```

Apply all pending migrations:

```bash
docker compose exec api alembic upgrade head
```

See the current migration revision:

```bash
docker compose exec api alembic current
```

---

## 🧪 Run Tests

Run all tests inside the API container:

```bash
docker compose exec api pytest -v
```

---

## 🛠️ Useful Commands

### View logs

```bash
# FastAPI logs
docker compose logs -f api

# Celery worker logs
docker compose logs -f worker

# PostgreSQL logs
docker compose logs -f postgres
```

### Restart the Celery worker

```bash
docker compose restart worker
```

### Open a shell inside the API container

```bash
docker compose exec api sh
```

### Stop services

```bash
docker compose down
```

### Remove services and database data

```bash
docker compose down -v
```

> [!WARNING]
> `docker compose down -v` removes the PostgreSQL volume permanently.> All database records will be lost.

---

## 🛡️ Security Considerations

- `.env` must remain private and should never be committed to Git.
- Use a long, random `SECRET_KEY` outside local development.
- Default PostgreSQL credentials are intended only for local development.
- Files are stored under `uploads/<user_id>/`.
- Every document operation filters by the authenticated user's ID, preventing cross-user file access.
- Production-ready improvements could include:
  - File extension, MIME-type, and size validation
  - Object storage such as MinIO or Amazon S3
  - HTTPS behind a reverse proxy
  - Rate limiting
  - Centralized logging and monitoring
  - Secret management

---

## 📚 Interactive Documentation

Once the application is running, explore and test all endpoints directly in your browser:

- **Swagger UI:** <http://localhost:8000/docs>
- **ReDoc:** <http://localhost:8000/redoc>
- **OpenAPI JSON:** <http://localhost:8000/openapi.json>

---

## 📌 License

This repository was created for **educational and portfolio purposes**.

Original user request:
عالیی میتونی لطفا به صورت یه فایل بدی که تو vscode بازش کنم؟