from fastapi import FastAPI, Depends
from app.core.config import settings
from app.db.session import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session


app = FastAPI(title=settings.APP_NAME)

@app.get("/health")
def health():
    return {"ok": True, "service": settings.APP_NAME}


@app.get("/admin/db-check")
def db_check(db: Session = Depends(get_db)):
    v = db.execute("SELECT 1").scalar()
    return {"ok": True, "db": v}