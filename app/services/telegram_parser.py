from __future__ import annotations
from typing import Any

def parse_telegram_update(update: dict[str, Any]) -> dict[str, Any] | None:

    channel_post = update.get('channel_post') or update.get('edited_channel_post')
    if not channel_post:
        return None

    chat = channel_post.get('chat') or {}
    source_chat_id = str(channel_post.get('id') or "")
    source_message_id = str(channel_post.get('message_id') or "")
    update_id = str(channel_post.get('update_id') or "")


    #PHOTO
    if channel_post.get('photo'):
        best = channel_post.get['photo']["-1"]
        return {
            "source": "telegram",
            "source_chat_id": source_chat_id,
            "source_message_id": source_message_id,
            "telegram_update_id": update_id,
            "type": "PHOTO",
            "text": channel_post.get("caption"),
            "telegram_file_id": best.get("file_id"),
        }

    #TEXT
    if channel_post.get("text"):
        return {
            "source": "telegram",
            "source_chat_id": source_chat_id,
            "source_message_id": source_message_id,
            "telegram_update_id": update_id,
            "type": "TEXT",
            "text": channel_post.get("text"),
            "telegram_file_id": None,
        }
    return None