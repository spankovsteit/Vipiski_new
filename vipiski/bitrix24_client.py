"""
Bitrix24 REST via incoming webhook — ``im.message.add``.

POST ``<webhook>/im.message.add.json`` with
``application/x-www-form-urlencoded`` body (``DIALOG_ID``, ``MESSAGE``).

Long messages are chunked at ``max_len`` (default 4000) and sent sequentially.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)


class Bitrix24SendError(RuntimeError):
    """Structured Bitrix24 delivery error with retry context."""

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


def send_bitrix24_message(
    webhook_url: str,
    dialog_id: str,
    text: str,
    max_len: int = 4000,
    *,
    timeout: float | None = None,
    max_retries: int | None = None,
) -> None:
    """
    Send ``text`` to Bitrix24 chat ``dialog_id`` (e.g. ``chat5294``).

    Split into chunks if longer than ``max_len``. Retries on connection/timeouts.
    """
    if timeout is None:
        timeout = float(os.environ.get("VIPISKI_BITRIX24_TIMEOUT", "120"))
    if max_retries is None:
        max_retries = int(os.environ.get("VIPISKI_BITRIX24_RETRIES", "4"))

    base = webhook_url.rstrip("/") + "/im.message.add.json"
    chunks: list[str] = []
    rest = text
    while rest:
        chunks.append(rest[:max_len])
        rest = rest[max_len:]

    for i, chunk in enumerate(chunks):
        data = urllib.parse.urlencode(
            {"DIALOG_ID": dialog_id, "MESSAGE": chunk}
        ).encode("utf-8")
        req = urllib.request.Request(base, data=data, method="POST")
        last_err: BaseException | None = None
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                if body.get("error"):
                    desc = body.get("error_description") or str(body["error"])
                    raise RuntimeError(f"Bitrix24 API error: {desc}")
                log.info(
                    "Bitrix24 part %d/%d sent (%d chars), message_id=%s",
                    i + 1,
                    len(chunks),
                    len(chunk),
                    body.get("result"),
                )
                last_err = None
                break
            except urllib.error.URLError as e:
                last_err = e
                wait = min(2**attempt, 30)
                log.warning(
                    "Bitrix24 send attempt %d/%d failed: %s; retry in %ds",
                    attempt + 1,
                    max_retries,
                    e,
                    wait,
                )
                if attempt < max_retries - 1:
                    time.sleep(wait)
            except RuntimeError as e:
                last_err = e
                break
        if last_err is not None:
            transient = isinstance(last_err, urllib.error.URLError)
            raise Bitrix24SendError(
                f"Bitrix24 send failed after {max_retries} attempt(s): {last_err}",
                transient=transient,
                attempts=max_retries,
            ) from last_err
