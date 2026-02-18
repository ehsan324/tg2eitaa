import uuid
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    source: Mapped[str] = mapped_column(String(32), nullable=False)  # telegram
    source_chat_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_message_id: Mapped[str] = mapped_column(String(64), nullable=False)

    type: Mapped[str] = mapped_column(String(16), nullable=False)  # TEXT | PHOTO
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    telegram_update_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    dedupe_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    media_assets: Mapped[list["MediaAsset"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="message", cascade="all, delete-orphan")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)

    type: Mapped[str] = mapped_column(String(16), nullable=False)  # PHOTO
    telegram_file_id: Mapped[str] = mapped_column(String(256), nullable=False)

    storage_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # برای آینده (S3/MinIO)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    message: Mapped["Message"] = relationship(back_populates="media_assets")


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # EITAA | BALE | ...
    chat_id: Mapped[str] = mapped_column(String(128), nullable=False)

    credentials_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="destination", cascade="all, delete-orphan")


class Delivery(Base):
    __tablename__ = "deliveries"
    __table_args__ = (
        UniqueConstraint("message_id", "destination_id", name="ux_delivery_msg_dest"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    destination_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    message: Mapped["Message"] = relationship(back_populates="deliveries")
    destination: Mapped["Destination"] = relationship(back_populates="deliveries")
