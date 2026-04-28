# Finance News Summary System

News text extraction + **BART** summarization (`facebook/bart-large-cnn`). **FastAPI** serves a small static UI; **ARQ** + **Redis** run URL summarization jobs (`POST` → `job_id` → poll `GET /jobs/...`).

Diagrams: [architecture](assets/system_architecture.png) · [pipeline](assets/worker_pipeline.png)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip && pip install -r requirements.txt
```

For **CUDA**, install PyTorch from [pytorch.org](https://pytorch.org) first if needed. NewsAPI scripts need a key (see `news_url_collector.py`).

## Run (local)

From the directory with `main.py` and `docker-compose.yml`:

```bash
chmod +x scripts/dev.sh   # once
./scripts/dev.sh          # starts Redis (Docker), API, ARQ worker
```

- UI: **http://127.0.0.1:8000/**  
- No Docker (e.g. local Redis): `SKIP_REDIS=1 ./scripts/dev.sh`  
- Env: `REDIS_HOST` (default `localhost`), `REDIS_PORT` (default `6379`)

Manual: `docker compose up -d` → `python main.py` → `arq arq_worker.WorkerSettings` (three terminals).

## API (short)

| Endpoint | Notes |
|----------|--------|
| `POST /api/v1/summarize-url` | `{ "url": "..." }` → `{ "job_id" }` or `503` |
| `GET /api/v1/jobs/{job_id}` | `complete` / `failed` / in-progress; `404` if missing |
| `POST /api/v1/search-and-summarize` | Placeholder (`{ "ok": true }`) |

## CLI (batch)

```bash
python news_url_collector.py --query "bitcoin" --start_date "2026-04-01" --end_date "2026-04-28" --language en --sort_by relevancy --page 1
python news_crawler.py --url_file_name output/json/url.json --workers 8
python summary_BART.py --num_beams 2 --max_output_length 60 --batch_size 4
```

## Troubleshooting

- **Docker / Redis**: use `SKIP_REDIS=1` if Redis runs elsewhere; fix Docker Desktop if compose fails.  
- **Jobs stuck**: start the **ARQ worker** and match Redis host/port with the API.
