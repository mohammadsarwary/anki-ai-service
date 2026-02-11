# Anki AI Service

AI-powered flashcard generation microservice — **project skeleton**.

> **Status:** Foundation only. No AI/LLM logic is implemented yet.  
> All generation endpoints return placeholder data.

---

## Quick Start

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## Project Structure

```
ai_service/
├── app/
│   ├── main.py                  # Application entry point & wiring
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── cards.py         # Route handlers (thin controllers)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py           # Pydantic request schemas
│   │   └── response.py          # Pydantic response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── card_generation_service.py  # Business logic layer
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py            # Centralized settings (env vars)
│   └── utils/
│       ├── __init__.py
│       └── logger.py            # Shared logging configuration
├── requirements.txt
└── README.md
```

---

## Architecture

The project follows **clean / layered architecture**:

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| **API** | `app/api/` | HTTP route handlers. Thin — validate input, call service, return response. |
| **Models** | `app/models/` | Pydantic schemas for request/response. Defines the API contract. |
| **Services** | `app/services/` | Core business logic. Independently testable, no HTTP dependency. |
| **Core** | `app/core/` | App-wide configuration, settings, shared infrastructure. |
| **Utils** | `app/utils/` | Cross-cutting helpers (logging, formatting, etc.). |

**Data flow:**

```
Client → API handler → Service → (future: AI provider) → Response model → Client
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe — returns `{"status": "ok"}` |
| `POST` | `/api/v1/cards/generate` | Generate a flashcard (placeholder response) |

### POST /api/v1/cards/generate

**Request body:**

```json
{
  "term": "ephemeral",
  "language": "en",
  "target_language": "fa",
  "level": "beginner"
}
```

**Response:**

```json
{
  "front": "ephemeral",
  "back": {
    "definition": "",
    "example": "",
    "phonetic": null
  },
  "difficulty": "medium"
}
```

---

## Future Extension Points

This skeleton is designed to be extended without restructuring:

1. **AI Provider Integration**
   - Add API keys to `core/config.py`
   - Implement the actual generation logic in `services/card_generation_service.py`
   - Consider a strategy/adapter pattern for swapping providers

2. **Database**
   - Add a `db/` package with connection pooling and repositories
   - Store generated cards for caching and analytics

3. **Authentication**
   - Add middleware or dependency injection in the API layer
   - Protect endpoints with API keys or JWT

4. **Batch Generation**
   - Add a new endpoint and request model for multi-term generation
   - Consider background tasks (Celery / FastAPI BackgroundTasks)

5. **Observability**
   - Structured JSON logging in `utils/logger.py`
   - Request tracing middleware with correlation IDs
   - Prometheus metrics endpoint

6. **Testing**
   - Add `tests/` directory with pytest
   - Unit tests for services, integration tests for API endpoints

---

## Configuration

Settings are managed via environment variables (or a `.env` file).  
See `app/core/config.py` for all available options.

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Anki AI Service | Application display name |
| `APP_VERSION` | 0.1.0 | Semantic version |
| `DEBUG` | false | Enable debug logging |
| `HOST` | 0.0.0.0 | Server bind address |
| `PORT` | 8000 | Server bind port |

---

## License

Private — not yet published.
