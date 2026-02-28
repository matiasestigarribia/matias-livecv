# Matias Live CV — Interactive Portfolio & Digital Twin

A full-stack portfolio website built as a **live CV** featuring a RAG-powered AI chatbot called **MatIAs** — a digital twin that answers questions about my professional experience, projects, and background in English, Spanish, and Portuguese.

> Open source. Fork it, adapt it, make it yours.

---

## Features

- **Multilingual** — English, Spanish, and Portuguese (server-side rendered, no flash)
- **MatIAs chatbot** — RAG pipeline with streaming SSE responses, powered by Groq (primary) and OpenAI (fallback)
- **Admin panel** — SQLAdmin for managing all content (profile, projects, skills, experiences, RAG documents)
- **Document ingestion** — Upload PDFs/TXTs through the admin to feed the chatbot's knowledge base
- **Image storage** — Cloudflare R2 for project images with cover photo management
- **Rate limiting** — SlowAPI to protect the chat endpoint
- **Health check endpoint** — `/health` keeps Neon and Cloud Run warm via cron

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.129, Python 3.13 |
| Database | PostgreSQL + pgvector (Neon serverless) |
| ORM / Migrations | SQLAlchemy 2.0 (async) + Alembic |
| AI / RAG | LangChain, Groq (llama-3.3-70b), OpenAI (gpt-4o-mini + embeddings) |
| Frontend | HTMX, Tailwind CSS, Jinja2 |
| Admin | SQLAdmin |
| Storage | Cloudflare R2 (S3-compatible) |
| Auth | JWT + Argon2 password hashing |
| Packaging | Poetry |
| Container | Docker |

---

## External Services Required

Before running the project, you need accounts and credentials for:

| Service | Purpose | Free tier? |
|---|---|---|
| [Neon](https://neon.tech) | PostgreSQL database with pgvector | Yes |
| [Groq](https://console.groq.com) | Primary LLM (fast inference) | Yes |
| [OpenAI](https://platform.openai.com) | Embeddings + backup LLM | Pay-as-you-go |
| [Cloudflare R2](https://developers.cloudflare.com/r2/) | Image storage | Yes (10 GB free) |

---

## Getting Started

### Prerequisites

- Python 3.13+
- [Poetry](https://python-poetry.org/docs/#installation)
- Node.js (only needed if you want to recompile Tailwind CSS)
- A Neon account with a project created

### 1. Clone the repository

```bash
git clone https://github.com/your-username/matias_live_cv.git
cd matias_live_cv
```

### 2. Install dependencies

```bash
poetry install
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in all values. See the [Environment Variables](#environment-variables) section below for details.

### 4. Enable pgvector on Neon

In your Neon dashboard (or via SQL), enable the `pgvector` extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

> This is required for the RAG chatbot. Neon supports pgvector natively.

### 5. Run database migrations

```bash
# Generate migration files from the existing models (first-time setup)
poetry run alembic revision --autogenerate -m "create initial tables"

# Apply migrations to your Neon database
poetry run alembic upgrade head
```

> On subsequent schema changes, run `alembic revision --autogenerate -m "description"` followed by `alembic upgrade head`.

### 6. Create an admin superuser

Create a script locally (do not commit it) to seed your first admin user:

```python
# create_superuser.py  (already in .gitignore)
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine
from app.core.security import get_password_hash
from app.models.users import User

async def create_superuser():
    async with AsyncSession(engine) as session:
        hashed_pw = get_password_hash("YourStrongPassword!")
        admin_user = User(
            username="admin",
            email="your@email.com",
            password=hashed_pw,
        )
        session.add(admin_user)
        await session.commit()
    print("Superuser created.")

if __name__ == "__main__":
    asyncio.run(create_superuser())
```

```bash
poetry run python create_superuser.py
```

### 7. Run the development server

```bash
poetry run uvicorn app.main:app --reload
```

The app will be available at `http://localhost:8000`.
The admin panel is at `http://localhost:8000/admin`.
The API docs are at `http://localhost:8000/docs`.

---

## Running with Docker

```bash
docker build -t matias-live-cv .
docker run -p 8000:8000 --env-file .env matias-live-cv
```

---

## Recompiling Tailwind CSS

The compiled CSS is included in `static/css/output.css`. If you modify templates or Tailwind config, recompile it:

```bash
npx tailwindcss -i static/css/input.css -o static/css/output.css --watch
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Neon asyncpg connection string (`postgresql+asyncpg://...?ssl=require`) |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens (generate with `secrets.token_hex(32)`) |
| `JWT_ALGORITHM` | JWT algorithm — use `HS256` |
| `JWT_EXPIRATION_MINUTES` | Admin session expiry in minutes |
| `OPENAI_API_KEY` | OpenAI API key (embeddings + backup LLM) |
| `GROQ_API_KEY` | Groq API key (primary LLM) |
| `PRIMARY_LLM` | Groq model name (e.g. `llama-3.3-70b-versatile`) |
| `BACKUP_LLM` | OpenAI model name (e.g. `gpt-4o-mini`) |
| `EMBEDDING_MODEL` | OpenAI embedding model (e.g. `text-embedding-3-small`) |
| `R2_ENDPOINT_URL` | Cloudflare R2 endpoint URL |
| `R2_ACCESS_KEY` | R2 access key ID |
| `R2_SECRET_KEY` | R2 secret access key |
| `R2_BUCKET_NAME` | R2 bucket name |
| `R2_PUBLIC_URL` | Public base URL for serving R2 files |

---

## Project Structure

```
matias_live_cv/
├── app/
│   ├── admin/          # SQLAdmin views and authentication backend
│   ├── core/           # Settings, database session, security, prompts, rate limiter
│   ├── models/         # SQLAlchemy ORM models
│   ├── routers/        # FastAPI routers (API endpoints + Jinja2 page routes)
│   ├── schemas/        # Pydantic request/response schemas
│   └── services/       # AI (RAG), image processing, Cloudflare R2 storage
├── migrations/         # Alembic migration scripts
│   └── versions/
├── static/
│   ├── css/            # Tailwind output.css
│   ├── js/             # HTMX interactions, neural-bg animation
│   └── images/
├── templates/
│   ├── base.html       # Navbar, footer, chat modal, all JS
│   ├── index.html      # App shell (HTMX swap target)
│   └── fragments/      # HTMX-swapped partial templates
├── agents/             # AI agent context documents (backend, frontend, QA)
├── alembic.ini
├── Dockerfile
├── pyproject.toml
└── tailwind.config.js
```

---

## Admin Panel

The SQLAdmin panel (`/admin`) lets you manage all content without touching the database directly:

- **Profile** — personal info, bio, social links
- **Experiences** — work history
- **Projects** — portfolio entries with images
- **Skills** — technical skills with proficiency levels
- **Spoken Languages** — human languages
- **RAG Documents** — knowledge base documents for the MatIAs chatbot (upload PDF/TXT per language)
- **Chat Logs** — conversation history with MatIAs
- **Contact Messages** — messages submitted through the contact form

---

## RAG Chatbot (MatIAs)

MatIAs is a digital twin powered by a retrieval-augmented generation (RAG) pipeline:

1. Upload documents (PDF, TXT, or Markdown) through the admin panel for each language (`en`, `es`, `pt`)
2. The system splits and embeds each document using OpenAI's embedding model and stores vectors in Neon (pgvector)
3. When a user sends a message, the query is embedded, the closest document chunks are retrieved, and a response is generated using Groq (with OpenAI as fallback)
4. Responses stream via Server-Sent Events (SSE) for a real-time typewriter effect

> The chatbot strictly answers only from the provided knowledge base — it does not hallucinate or answer off-topic questions.

---

## API Endpoints

Interactive docs available at `/docs` (Swagger UI) and `/redoc`.

Key routes:

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check (database ping) |
| `GET` | `/api/v1/profile` | Fetch profile data |
| `GET` | `/api/v1/experiences` | List work experiences |
| `GET` | `/api/v1/projects` | List portfolio projects |
| `GET` | `/api/v1/skills` | List skills |
| `POST` | `/api/v1/chat/stream` | Stream a chat response (SSE) |
| `POST` | `/api/v1/contactmessage` | Submit a contact message |

---

## License

MIT — feel free to fork and adapt this project for your own portfolio.

---

## Author

**Matias Pedro Estigarribia**
[matiasp.estigarribia@gmail.com](mailto:matiasp.estigarribia@gmail.com)
