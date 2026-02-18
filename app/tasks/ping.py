from __future__ import annotations
from datetime import datetime, timezone

from app.core.celery_app import celery

@celery.task(name="app.tasks.ping.ping")
def ping(payload: str = "pong") -> dict:
    return {
        "ok": True,
        "payload": payload,
        "ts": datetime.now(timezone.utc).timestamp(),
    }