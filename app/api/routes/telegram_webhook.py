from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db.session import get_db
from app.db.models import Message, MediaAsset
from app.services.telegram_parser import parse_telegram_update

from app.services.orchestrator import fanout_message


router = APIRouter(prefix="/webhook/telegram", tags=["telegram"])


@router.post("")
async def telegram_webhook(
        request: Request,
        db: Session = Depends(get_db),
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret token")

    update = await request.json()
    parsed = parse_telegram_update(update)
    if not parsed:
        return {"ok": True, "ignored": True}

    dedupe_key = f'{parsed["source_chat_id"]}:{parsed["source_message_id"]}'

    msg = Message(
        source="telegram",
        source_chat_id=parsed["source_chat_id"],
        source_message_id=parsed["source_message_id"],
        telegram_update_id=parsed.get("telegram_update_id"),
        type=parsed["type"],
        text=parsed.get("text"),
        dedupe_key=dedupe_key,
    )
    db.add(msg)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"ok": True, "deduped": True}

    db.refresh(msg)

    created = fanout_message(db, msg.id)

    if parsed["type"] == "PHOTO" and parsed.get("telegram_file_id"):
        db.add(
            MediaAsset(
                message_id=msg.id,
                type="PHOTO",
                telegram_file_id=parsed["telegram_file_id"],
                status="PENDING",
            )
        )
        db.commit()

    return {"ok": True, "message_id": str(msg.id), "type": msg.type}
