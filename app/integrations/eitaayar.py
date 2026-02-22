# app/integrations/eitaayar.py
from __future__ import annotations

import requests


class EitaaTransientError(RuntimeError):
    pass


class EitaaPermanentError(RuntimeError):
    pass


def _url(token: str, method: str) -> str:
    return f"https://eitaayar.ir/api/{token}/{method}"


def send_message(*, token: str, chat_id: str, text: str) -> dict:
    """
    Send a TEXT message via eitaayar gateway.
    Returns response dict if ok.
    Raises:
      - EitaaTransientError on retryable issues
      - EitaaPermanentError on non-retryable issues
    """

    if chat_id.startswith("@"):
        chat_id = chat_id[1:]

    try:
        r = requests.post(
            _url(token, "sendMessage"),
            data={"chat_id": chat_id, "text": text},
            timeout=20,
        )
    except (requests.Timeout, requests.ConnectionError) as e:
        raise EitaaTransientError(f"network error: {e}") from e

    if r.status_code >= 500:
        raise EitaaTransientError(f"eitaayar 5xx: {r.status_code} {r.text[:200]}")
    if r.status_code >= 400:
        raise EitaaPermanentError(f"eitaayar 4xx: {r.status_code} {r.text[:200]}")

    try:
        data = r.json()
    except Exception as e:
        raise EitaaTransientError(f"invalid json response: {e}, body={r.text[:200]}") from e

    if not data.get("ok", False):
        raise EitaaPermanentError(f"eitaayar ok=false: {data}")

    return data