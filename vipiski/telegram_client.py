"""
Telegram Bot API via **urllib** (no pyTelegramBotAPI dependency).

API
---
POST ``https://api.telegram.org/bot<token>/sendMessage`` with
``application/x-www-form-urlencoded`` body (``urlencode``).

Long messages
-------------
Telegram caps message length (~4096). We chunk at ``max_len`` (default 4000 to
leave margin) and send sequentially.

Reliability
-----------
``URLError`` (timeouts, SSL handshake failures, corporate firewalls) triggers
retries with backoff. Set ``VIPISKI_TELEGRAM_RETRIES`` / ``VIPISKI_TELEGRAM_TIMEOUT``
via environment (read in ``send_telegram_message`` from ``os.environ``).
"""

from __future__ import annotations

import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

class TelegramSendError(RuntimeError):
    """Structured Telegram delivery error with retry context."""

    def __init__(
        self,
        message: str,
        *,
        transient: bool,
        attempts: int,
    ) -> None:
        super().__init__(message)
        self.transient = transient
        self.attempts = attempts


def send_telegram_message(
    token: str,
    chat_id: str,
    text: str,
    max_len: int = 4000,
    *,
    timeout: float | None = None,
    max_retries: int | None = None,
) -> None:
    """
    Send ``text`` to ``chat_id``; split into chunks if longer than ``max_len``.

    Retries on connection/SSL/timeouts (common behind corporate proxies or flaky
    networks). After all retries fail, raises ``TelegramSendError`` with a
    ``transient`` flag.
    """
    if timeout is None:
        timeout = float(os.environ.get("VIPISKI_TELEGRAM_TIMEOUT", "180"))
    if max_retries is None:
        max_retries = int(os.environ.get("VIPISKI_TELEGRAM_RETRIES", "4"))

    base = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks: list[str] = []
    rest = text
    while rest:
        chunks.append(rest[:max_len])
        rest = rest[max_len:]

    for i, chunk in enumerate(chunks):
        data = urllib.parse.urlencode(
            {"chat_id": chat_id, "text": chunk}
        ).encode("utf-8")
        req = urllib.request.Request(base, data=data, method="POST")
        last_err: BaseException | None = None
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    body = resp.read()
                    if resp.status != 200:
                        raise RuntimeError(f"Telegram HTTP {resp.status}: {body!r}")
                log.info(
                    "Telegram part %d/%d sent (%d chars)",
                    i + 1,
                    len(chunks),
                    len(chunk),
                )
                last_err = None
                break
            except urllib.error.URLError as e:
                last_err = e
                wait = min(2**attempt, 30)
                log.warning(
                    "Telegram send attempt %d/%d failed: %s; retry in %ds",
                    attempt + 1,
                    max_retries,
                    e,
                    wait,
                )
                if attempt < max_retries - 1:
                    time.sleep(wait)
        if last_err is not None:
            raise TelegramSendError(
                f"Telegram send failed after {max_retries} attempt(s): {last_err}",
                transient=True,
                attempts=max_retries,
            ) from last_err
