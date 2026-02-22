# app/services/orchestrator.py
from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import Destination, Delivery
from app.tasks.deliveries import process_delivery


def fanout_message(db: Session, message_id) -> int:

    destinations = db.query(Destination).filter(Destination.is_active.is_(True)).all()
    created = 0

    for dest in destinations:
        d = Delivery(message_id=message_id, destination_id=dest.id, status="PENDING", attempt_count=0)
        db.add(d)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue

        db.refresh(d)
        process_delivery.delay(str(d.id))
        created += 1

    return created