"""Tests for telegram retry/error handling."""

from __future__ import annotations

import urllib.error

import pytest

from vipiski.telegram_client import TelegramSendError, send_telegram_message


def test_telegram_raises_transient_structured_error(monkeypatch):
    def _fail(*args, **kwargs):
        raise urllib.error.URLError("timeout")

    monkeypatch.setattr("urllib.request.urlopen", _fail)

    with pytest.raises(TelegramSendError) as ei:
        send_telegram_message(
            "token",
            "chat",
            "hello",
            max_retries=1,
            timeout=0.01,
        )
    err = ei.value
    assert err.transient is True
    assert err.attempts == 1

