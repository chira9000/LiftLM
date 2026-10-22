# LiftAI

[![CI](https://github.com/chira9000/LiftLM/actions/workflows/ci.yml/badge.svg)](https://github.com/chira9000/LiftLM/actions/workflows/ci.yml)

An AI-powered lifting coach that combines workout tracking, gym analytics, progressive-overload recommendations, and an LLM chat interface.

## Architecture

```
User → Next.js frontend → FastAPI → PostgreSQL
                              ↓
                 Analytics + Progression Engine
                              ↓
                         LLM Service
```

- **Deterministic calculations** (volume, e1RM, PRs, progression scores) run in Python — never delegated to the LLM
- **LLM coach** receives structured analytics context, not raw workout logs
- **Pluggable LLM providers**: `mock` (default), `ollama`, `mlx` (Apple Silicon via mlx-lm)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API seeds a demo account on first startup with 8 weeks of sample workout data.

### 3. Start the frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Demo credentials

| Email | Password |
|-------|----------|
| demo@liftai.app | demo1234 |

## Features

### Workout Tracking
Log workouts with exercises, sets, reps, weight, RPE, and dates via the **Log Workout** page or `POST /api/workouts`.

### Gym Analytics
- Training volume trends
- Estimated 1RM (Epley formula)
- Personal records
- Exercise frequency
- Per-exercise performance charts

### Progressive Overload
Deterministic engine analyzes:
- **Consistency** — training frequency
- **RPE management** — intensity sweet spot (7–8.5)
- **Volume trend** — recent vs prior volume
- **Long-term progression** — e1RM over time
- **Recent performance** — last session vs previous

Outputs a **Progression Score** (0–100) and concrete weight/reps/sets recommendations.

### AI Coach
Chat interface powered by structured analytics, a curated training-science knowledge base (with PubMed citations), and Reddit community search (lifting subreddits). Example questions:
- "How is my bench progressing?"
- "What should I do for bench today?"
- "Why have I stopped progressing on squat?"

Each reply can include linked Reddit sources. Toggle with `REDDIT_ENABLED` in `backend/.env`.

### Training-Science Knowledge Base
The coach keyword-matches each question against a curated set of training-science topics — exercise selection, training principles, progressive overload, volume, intensity, RPE/RIR, recovery, programming, deloading, technique, common plateaus, strength standards, and nutrition basics (`backend/app/services/knowledge/library.py`). Matched topics are injected into the LLM's context alongside the user's analytics, and each comes with real supporting PubMed citations.

At request time the coach also queries the [NCBI E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25501/) live to supplement the curated citations with fresh PubMed results (`backend/app/services/knowledge/pubmed.py`), cached in-memory to avoid hammering NCBI. Replies surface a **PubMed research** section with links to the cited studies. Toggle with `KNOWLEDGE_ENABLED` / `PUBMED_ENABLED` in `backend/.env`.

To enable live Reddit search, create a free app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) (type: **script**), then set:

```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=LiftAI/1.0 by u/yourusername
```

Without credentials the coach still works from analytics; community sources may be empty if Reddit blocks unauthenticated requests.

## LLM Configuration

Set `LLM_PROVIDER` in `backend/.env`:

| Provider | Description |
|----------|-------------|
| `mock` | Rule-based responses (default, no model needed) |
| `mlx` | Apple Silicon via `mlx-lm` (~1–3 GB, recommended on Mac) |
| `ollama` | Local models via [Ollama](https://ollama.ai) (~1–5 GB small variants) |
| `openai` | vLLM, SGLang, or any OpenAI-compatible `/v1/chat/completions` server |

### Compact local LLM (recommended for laptops)

For a coach that runs fully offline without a 20+ GB download, use a **4B or smaller** quantized model.

**Apple Silicon (MLX)** — no separate server, ~2.5 GB download:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-mlx.txt
```

```env
LLM_PROVIDER=mlx
LLM_MODEL=mlx-community/Qwen3-4B-Instruct-4bit
```

Even smaller (~1 GB): `mlx-community/Qwen3-1.7B-4bit`

**Ollama** — works on Mac, Linux, and Windows:

```bash
ollama pull qwen3:4b    # ~2.5 GB
# ollama pull qwen3:1.7b  # ~1.2 GB, faster but weaker
```

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:4b
LLM_BASE_URL=http://localhost:11434
```

The model loads once and stays in memory; first chat may take a few seconds while weights download.

### Qwen3-32B via Ollama (high-end GPU)

Requires ~20 GB VRAM (Q4) or ~35 GB (Q8). A 24 GB GPU (e.g. RTX 4090) runs Q4 comfortably.

```bash
ollama pull qwen3:32b
```

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:32b
LLM_BASE_URL=http://localhost:11434
LLM_THINK=false
```

Smaller/larger Qwen3 variants: `qwen3:8b`, `qwen3:14b`, `qwen3:235b` (MoE, needs multi-GPU).

### vLLM / SGLang (production GPU server)

Serve `Qwen/Qwen3-32B` with [vLLM](https://docs.vllm.ai) or [SGLang](https://github.com/sgl-project/sglang), then point the backend at the OpenAI-compatible endpoint:

```env
LLM_PROVIDER=openai
LLM_MODEL=Qwen/Qwen3-32B
LLM_BASE_URL=http://localhost:8001/v1
LLM_TIMEOUT=300
```

### MLX (Apple Silicon)

See **Compact local LLM** above. Legacy unquantized default:

```env
LLM_PROVIDER=mlx
LLM_MODEL=Qwen/Qwen3-8B
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Login |
| GET | `/api/workouts` | List workouts |
| POST | `/api/workouts` | Create workout |
| GET | `/api/analytics/dashboard` | Dashboard stats |
| GET | `/api/analytics/exercises` | Per-exercise analytics |
| GET | `/api/progression` | Progression recommendations |
| POST | `/api/coach/chat` | AI coach chat |

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Testing

Unit tests cover the deterministic core: e1RM estimation, the progression scoring functions, muscle-group detection, and the intent classifier.

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Project Structure

```
LiftLM/
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # FastAPI routes
│   │   ├── models/                # SQLAlchemy models
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/
│   │   │   ├── analytics/         # Volume, e1RM, trends
│   │   │   ├── progression/       # Overload engine + scores
│   │   │   ├── social/            # Reddit (extensible) community research
│   │   │   ├── knowledge/         # Curated training-science KB + live PubMed search
│   │   │   └── llm/               # Coach service, intent + muscle-group classifiers
│   │   ├── exercise_catalog.py    # ~180-exercise library seeded on startup
│   │   ├── seed.py                # Sample data
│   │   └── main.py
│   ├── tests/                     # pytest unit tests
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                   # Next.js pages
│       ├── components/            # UI components + charts
│       └── lib/api.ts             # API client
└── docker-compose.yml
```

## License

MIT
