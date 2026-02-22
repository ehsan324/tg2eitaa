from fastapi import FastAPI, Depends
from app.core.config import settings
from app.db.session import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from app.tasks.ping import ping
from app.core.celery_app import celery
import json
from app.db.models import Destination

from app.api.routes.telegram_webhook import router as telegram_router

app = FastAPI(title=settings.APP_NAME)

app.include_router(telegram_router, tags=["telegram"])


@app.get("/health")
def health():
    return {"ok": True, "service": settings.APP_NAME}


@app.get("/admin/db-check")
def db_check(db: Session = Depends(get_db)):
    v = db.execute("SELECT 1").scalar()
    return {"ok": True, "db": v}


@app.post("/admin/celery-ping")
def celery_ping():
    job = ping.delay("hello from api")
    return {"queued": True, "task_id": job.id}


@app.get("/admin/tasks/{task_id}")
def task_status(task_id: str):
    res = AsyncResult(task_id, app=celery)
    return {"task_id": task_id, "state": res.state, "result": res.result}




@app.post("/admin/bootstrap-destination")
def bootstrap_destination(db: Session = Depends(get_db)):
    existing = db.query(Destination).filter(Destination.kind == "EITAA").first()
    if existing:
        return {"ok": True, "created": False, "destination_id": str(existing.id)}

    dest = Destination(
        kind="EITAA",
        chat_id=settings.DEFAULT_EITAA_CHAT_ID,
        credentials_json=json.dumps({"token": settings.EITAA_TOKEN}) if settings.EITAA_TOKEN else None,
        is_active=True,
    )
    db.add(dest)
    db.commit()
    db.refresh(dest)
    return {"ok": True, "created": True, "destination_id": str(dest.id)}