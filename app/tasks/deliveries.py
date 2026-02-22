# app/tasks/deliveries.py
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone

from app.core.celery_app import celery
from app.db.session import Sessionlocal
from app.db.models import Delivery, Message, Destination

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.deliveries.process_delivery")
def process_delivery(delivery_id: str) -> None:
    db = Sessionlocal()
    try:
        did = uuid.UUID(delivery_id)

        delivery = db.query(Delivery).filter(Delivery.id == did).one()
        msg = db.query(Message).filter(Message.id == delivery.message_id).one()
        dest = db.query(Destination).filter(Destination.id == delivery.destination_id).one()

        # 1) برو SENDING
        delivery.status = "SENDING"
        delivery.attempt_count += 1
        db.commit()

        logger.info("SIMULATE SEND: msg=%s type=%s -> %s(%s)", msg.id, msg.type, dest.kind, dest.chat_id)

        delivery.status = "SENT"
        delivery.sent_at = datetime.now(timezone.utc)
        db.commit()

    finally:
        db.close()