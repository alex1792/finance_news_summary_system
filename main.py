import os
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job, JobStatus
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq_pool = await create_pool(
        RedisSettings(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
        )
    )
    yield
    await app.state.arq_pool.close()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

"""
Using Pydantic, the attribute name of each class should match with json key sent from frontent.
"""


class SearchAndSummarize(BaseModel):
    keyword: str
    start_date: str
    end_date: str


class SummarizeUrl(BaseModel):
    url: str


@app.get("/")
def read_root():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/v1/search-and-summarize")
def search_and_summarize(body: SearchAndSummarize):
    """
    use keyword to search news, with start_time and end_time
    then return the summary of the news in this time period

    1. get keyword, start_time, end_time
    2. call news_url_collector(keyword, start_time, end_time)
    3. from url.json, call news_crawler.crawl_all_news_parallel(num_workers)
    4. from news.json, call summaryBART.summarize_news(filename)
    5. return the summary of the news to frontend
    """
    return {"ok": True}


@app.post("/api/v1/summarize-url")
async def summmarize_url(body: SummarizeUrl):
    """
    Enqueue summarize_url_task; client polls GET /api/v1/jobs/{job_id}.
    """
    try:
        pool = app.state.arq_pool
        job = await pool.enqueue_job("summarize_url_task", body.url)
        return {"job_id": job.job_id}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "enqueue_failed",
                "message": str(e),
            },
        ) from e


@app.get("/api/v1/jobs/{job_id}")
async def get_job_result(job_id: str):
    pool = app.state.arq_pool
    job = Job(job_id, pool)
    status = await job.status()

    if status == JobStatus.not_found:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "job_not_found",
                "message": "Job not found",
                "job_id": job_id,
            },
        )

    if status == JobStatus.complete:
        try:
            result = await job.result()
        except Exception as e:
            return {"status": "failed", "error": str(e), "job_id": job_id}
        return {"status": "complete", "result": result, "job_id": job_id}

    return {"status": status.name, "job_id": job_id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
