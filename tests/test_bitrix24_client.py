import json
from unittest.mock import MagicMock, patch

import pytest

from vipiski.bitrix24_client import Bitrix24SendError, send_bitrix24_message


def test_send_bitrix24_message_splits_long_text():
    calls: list[bytes] = []

    def fake_urlopen(req, timeout=0):
        calls.append(req.data)
        resp = MagicMock()
        resp.read.return_value = json.dumps({"result": 1}).encode("utf-8")
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    text = "x" * 5000
    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        send_bitrix24_message("https://example/rest/1/secret/", "chat1", text)

    assert len(calls) == 2
    assert len(calls[0]) > 0
    assert len(calls[1]) > 0


def test_send_bitrix24_message_api_error_is_non_transient():
    def fake_urlopen(req, timeout=0):
        resp = MagicMock()
        resp.read.return_value = json.dumps(
            {"error": "ACCESS_DENIED", "error_description": "nope"}
        ).encode("utf-8")
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        with pytest.raises(Bitrix24SendError) as exc:
            send_bitrix24_message("https://example/rest/1/secret/", "chat1", "hi")
    assert exc.value.transient is False
