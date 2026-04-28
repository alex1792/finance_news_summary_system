"""
ARQ worker: from project directory run:
  arq arq_worker.WorkerSettings
Requires Redis (e.g. docker compose up -d).
"""
from __future__ import annotations

import asyncio
import os

from arq.connections import RedisSettings

from news_crawler import NewsCrawler
from summary_BART import SummaryBART

news_crawler = NewsCrawler(load_urls=False)
summaryBART = SummaryBART(num_beams=4, max_output_length=80)


def _redis_settings() -> RedisSettings:
    return RedisSettings(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
    )


def _summarize_url_sync(url: str, crawler: NewsCrawler, summarizer: SummaryBART) -> dict:
    """Blocking: HTTP fetch, extract text, BART — runs in a thread pool."""
    item = {
        "source": None,
        "title": None,
        "author": None,
        "description": None,
        "url": url,
        "publishedAt": None,
    }
    article_json = crawler.crawl_news(item)
    content = (article_json.get("content") or "").strip()
    if not content:
        return {"ok": False, "error": "No extractable content", "url": url}
    summary = summarizer.summarize(article_json["content"])
    return {
        "ok": True,
        "content": content,
        "summary": summary,
        "url": url,
        "title": article_json.get("title"),
    }


async def summarize_url_task(ctx: dict, url: str) -> dict:
    _ = ctx
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _summarize_url_sync,
        url,
        news_crawler,
        summaryBART,
    )


class WorkerSettings:
    redis_settings = _redis_settings()
    functions = [summarize_url_task]
