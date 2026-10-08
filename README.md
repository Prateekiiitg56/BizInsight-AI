# BizInsight AI

BizInsight AI is a customer-feedback analytics platform. Upload a CSV of reviews and get sentiment scoring, risk alerts, complaint clustering, and an AI assistant that answers questions using only your own reviews.

- **Frontend:** Next.js 14 (App Router), React, Tailwind CSS, Recharts
- **Backend:** FastAPI, SQLite (dev) / PostgreSQL (prod), ChromaDB
- **ML / NLP:** NLTK VADER sentiment, BERTopic + UMAP + HDBSCAN clustering, FastEmbed embeddings, LangChain RAG over OpenRouter

---

## Features

| Feature | What it does |
|---|---|
| **Sentiment dashboard** | Scores every review (VADER, −1 to +1); shows average sentiment, positive/neutral/negative split, a daily trend chart and top keywords. Export the scored data as CSV. |
| **Risk alerts** | Low / medium / high risk from the share of negative reviews (25 % and 40 % thresholds), with the top issue keywords. |
| **Topic clustering** | Groups negative (or positive) reviews into themes such as *Delivery Issues* or *Product Quality Issues* using BERTopic, running as a background job. |
| **AI assistant (RAG)** | Answers questions grounded only in the signed-in user's reviews, with source quotes. Works without an LLM key in retrieval-only mode. |
| **Public demo** | `/chat` lets signed-out visitors try the assistant on a bundled sample dataset — no account needed, and no user data is exposed. |
| **Accounts** | Username/password and optional Google sign-in (JWT). The first account becomes the admin, who can manage users. |

Every user's data — reviews, dashboards, clustering jobs and vectors — is isolated from every other user's.

---

## Repository layout

```text
BizInsight-AI/
├── backend/
│   ├── bizinsight_api/        # FastAPI app: main.py, config.py, routes/, models/
│   ├── rag_api/               # RAG assistant: chains, vector store, per-user indexing
│   ├── clustering/            # BERTopic clustering pipeline
│   ├── data/demo_reviews.csv  # Sample dataset for the public demo chat
│   ├── tests/                 # pytest suite
│   ├── database.py            # SQLite / PostgreSQL access
│   ├── sentiment.py           # VADER scoring
│   ├── download_model.py      # Build-time model downloads
│   ├── sync_vectors.py        # Rebuild the vector index from the database
│   └── Dockerfile
├── frontend/                  # Next.js app (src/app, src/components, src/lib)
├── data/samples/              # Sample review CSVs to try uploads with
├── docs/ARCHITECTURE.md
├── Dockerfile, cloudbuild.yaml  # Backend image for Google Cloud Run
└── render.yaml                  # Backend blueprint for Render
```

---

## Running locally

**Prerequisites:** Python 3.11+, Node.js 20+.

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python download_model.py           # VADER lexicon + clustering model
cp .env.example .env               # then set JWT_SECRET (and optionally OPENROUTER_API_KEY)
uvicorn bizinsight_api.main:app --port 8001 --reload
```

API docs: http://localhost:8001/docs

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local         # NEXT_PUBLIC_API_URL=http://localhost:8001
npm install
npm run dev
```

Open http://localhost:3000 and create an account (the first account is the admin).

### 3. Tests and checks

```bash
cd backend && python -m pytest -q tests
cd frontend && npm run lint && npx tsc --noEmit && npm run build
```

CI runs the same checks on every push and pull request (`.github/workflows/ci.yml`).

---

## Configuration

### Backend (`backend/.env.example` lists everything)

| Variable | Required | Description |
|---|---|---|
| `JWT_SECRET` | **Yes, in production** | Long random string used to sign login tokens. |
| `FRONTEND_URL` | Yes, in production | Comma-separated frontend origin(s) allowed by CORS. |
| `OPENROUTER_API_KEY` | No | Enables AI-written answers. Without it the assistant lists the most relevant reviews. |
| `GOOGLE_CLIENT_ID` | No | Enables Google sign-in (must match the frontend's client ID). |
| `DATABASE_URL` | No | PostgreSQL URL. Defaults to a local SQLite file. |
| `CHROMA_HOST` / `CHROMA_PORT` | No | Remote ChromaDB server. Defaults to a local `chroma_db/` directory. |
| `LLM_MODEL` | No | OpenRouter model slug (default `openai/gpt-4o-mini`). |

### Frontend (`frontend/.env.example`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL, e.g. `https://your-api.onrender.com`. |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Optional. Shows the "Continue with Google" button. |

---

## Deployment

**Frontend → Vercel.** Import the repo, set the root directory to `frontend` (or use the root `vercel.json`), and set `NEXT_PUBLIC_API_URL` (plus `NEXT_PUBLIC_GOOGLE_CLIENT_ID` if used). For Google sign-in, add the site origin as an authorized JavaScript origin and redirect URI in Google Cloud Console.

**Backend → any of:**
- **Render:** `render.yaml` is a ready blueprint (it generates `JWT_SECRET`; fill in `FRONTEND_URL` and optional keys).
- **Google Cloud Run:** `cloudbuild.yaml` builds the root `Dockerfile` and deploys it.
- **Docker anywhere / Hugging Face Spaces:** `docker build -t bizinsight-api backend && docker run -p 8080:8080 -e JWT_SECRET=... bizinsight-api`

**Production notes**
- Use PostgreSQL (`DATABASE_URL`) on hosts with ephemeral disks; SQLite data is lost when the container restarts.
- The vector index is derived data: it rebuilds automatically from the database for each user, or all at once with `python sync_vectors.py`.
- Clustering jobs are held in memory, so run the API as a single instance (or one worker) unless you add a shared job store.
- Clustering loads PyTorch models and needs roughly 1 GB+ of RAM; the rest of the API runs in ~512 MB.

---

## CSV format

Sample files to try are in [`data/samples/`](data/samples). The file needs a column named `review` (case-insensitive) with one review per row. Other columns are ignored. Maximum size is 10 MB (configurable with `MAX_UPLOAD_MB`).

```csv
review
"Delivery was two days late."
"Great quality, would buy again!"
```

---

## License

See [LICENSE.md](LICENSE.md). Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

**Author:** Prateek Singh
