# LiftAI

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
Chat interface powered by structured analytics. Example questions:
- "How is my bench progressing?"
- "What should I do for bench today?"
- "Why have I stopped progressing on squat?"

## LLM Configuration

Set `LLM_PROVIDER` in `backend/.env`:

| Provider | Description |
|----------|-------------|
| `mock` | Rule-based responses (default, no model needed) |
| `ollama` | Local Qwen via [Ollama](https://ollama.ai) |
| `mlx` | Apple Silicon via `mlx-lm` (LoRA-ready) |

For Ollama:
```bash
ollama pull qwen2.5:1.5b-instruct
# Set LLM_PROVIDER=ollama and LLM_MODEL=qwen2.5:1.5b-instruct
```

For MLX (Apple Silicon):
```bash
pip install mlx-lm
# Set LLM_PROVIDER=mlx and LLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
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
│   │   │   └── llm/               # Coach service (mock/ollama/mlx)
│   │   ├── seed.py                # Sample data
│   │   └── main.py
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
