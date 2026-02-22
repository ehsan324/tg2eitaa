from __future__ import annotations
from datetime import datetime, timezone

from celery import shared_task

@shared_task(name="app.tasks.ping.ping")
def ping(payload: str = "pong") -> dict:
    return {
        "ok": True,
        "payload": payload,
        "ts": datetime.now(timezone.utc).timestamp(),
    }