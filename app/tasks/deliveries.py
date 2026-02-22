from __future__ import annotations

import json
import uuid
import logging
from datetime import datetime, timezone

from app.core.celery_app import celery
from app.core.config import settings
from app.db.session import Sessionlocal
from app.db.models import Delivery, Message, Destination
from app.integrations.eitaayar import send_message, EitaaTransientError, EitaaPermanentError

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.deliveries.process_delivery", bind=True, max_retries=10)
def process_delivery(self, delivery_id: str) -> None:
    db = Sessionlocal()
    try:
        did = uuid.UUID(delivery_id)

        claimed = (
            db.query(Delivery)
            .filter(Delivery.id == did, Delivery.status.in_(["PENDING", "RETRYING"]))
            .update(
                {
                    Delivery.status: "SENDING",
                    Delivery.attempt_count: Delivery.attempt_count + 1,
                    Delivery.last_error: None,
                },
                synchronize_session=False,
            )
        )
        if claimed == 0:
            db.commit()
            return
        db.commit()

        # 2) Load data
        delivery = db.query(Delivery).filter(Delivery.id == did).one()
        msg = db.query(Message).filter(Message.id == delivery.message_id).one()
        dest = db.query(Destination).filter(Destination.id == delivery.destination_id).one()

        if msg.type != "TEXT":
            db.query(Delivery).filter(Delivery.id == did).update(
                {
                    Delivery.status: "FAILED",
                    Delivery.last_error: f"Unsupported type in phase5: {msg.type}",
                },
                synchronize_session=False,
            )
            db.commit()
            return

        # 4) توکن را از credentials_json یا env بگیر
        creds = {}
        if dest.credentials_json:
            try:
                creds = json.loads(dest.credentials_json)
            except Exception:
                creds = {}

        token = creds.get("token") or settings.EITAA_TOKEN
        if not token:
            raise EitaaPermanentError("Missing EITAA token")

        if not dest.chat_id:
            raise EitaaPermanentError("Missing destination chat_id")

        text = msg.text or ""

        send_message(token=token, chat_id=dest.chat_id, text=text)

        db.query(Delivery).filter(Delivery.id == did).update(
            {
                Delivery.status: "SENT",
                Delivery.sent_at: datetime.now(timezone.utc),
                Delivery.last_error: None,
            },
            synchronize_session=False,
        )
        db.commit()
        logger.info("SENT delivery=%s msg=%s -> EITAA(%s)", did, msg.id, dest.chat_id)

    except EitaaPermanentError as e:
        db.query(Delivery).filter(Delivery.id == uuid.UUID(delivery_id)).update(
            {Delivery.status: "FAILED", Delivery.last_error: str(e)},
            synchronize_session=False,
        )
        db.commit()

    except EitaaTransientError as e:
        db.query(Delivery).filter(Delivery.id == uuid.UUID(delivery_id)).update(
            {Delivery.status: "RETRYING", Delivery.last_error: str(e)},
            synchronize_session=False,
        )
        db.commit()

        retries = int(getattr(self.request, "retries", 0))
        countdown = min(60 * (2 ** min(retries, 6)), 6 * 60 * 60)  # تا ۶ ساعت
        raise self.retry(exc=e, countdown=countdown)

    finally:
        db.close()