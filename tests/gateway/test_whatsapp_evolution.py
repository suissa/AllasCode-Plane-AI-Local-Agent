import json

import pytest

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import MessageType
from gateway.platforms.whatsapp import WhatsAppAdapter


def _adapter(tmp_path=None, **extra):
    base = {
        "api_key": "admin-key",
        "instance_token": "instance-token",
        "auto_start": False,
        "build_on_start": False,
        "webhook_port": 0,
    }
    if tmp_path is not None:
        base["service_path"] = str(tmp_path)
    base.update(extra)
    return WhatsAppAdapter(PlatformConfig(enabled=True, extra=base))


def test_evolution_env_forces_requested_port(tmp_path):
    (tmp_path / ".env.example").write_text(
        "SERVER_PORT=8008\nGLOBAL_API_KEY=from-example\nDATABASE_SAVE_MESSAGES=false\n",
        encoding="utf-8",
    )
    adapter = _adapter(tmp_path, service_port=9991, api_key="")

    adapter._ensure_evolution_env()

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "SERVER_PORT=9991" in env_text
    assert "SERVER_PORT=8008" not in env_text
    assert adapter._evolution_api_key == "from-example"


@pytest.mark.asyncio
async def test_send_uses_evolution_text_endpoint(monkeypatch):
    adapter = _adapter()
    adapter._running = True
    adapter._http_session = object()
    calls = []

    async def fake_request(method, path, *, json_data=None, admin=False, timeout=30):
        calls.append((method, path, json_data, admin, timeout))
        return 200, {"data": {"Info": {"ID": "msg-1"}}}

    monkeypatch.setattr(adapter, "_evolution_request", fake_request)

    result = await adapter.send("5511999999999@s.whatsapp.net", "hello")

    assert result.success is True
    assert result.message_id == "msg-1"
    assert calls == [
        (
            "POST",
            "/send/text",
            {"number": "5511999999999@s.whatsapp.net", "text": "hello", "formatJid": False},
            False,
            30,
        )
    ]


@pytest.mark.asyncio
async def test_evolution_webhook_payload_becomes_message_event():
    adapter = _adapter()
    payload = {
        "event": "Message",
        "data": {
            "Info": {
                "ID": "abc123",
                "Chat": "5511999999999@s.whatsapp.net",
                "Sender": "5511999999999@s.whatsapp.net",
            },
            "PushName": "Alice",
            "Message": {"conversation": "oi hermes"},
        },
    }

    event = await adapter._build_evolution_message_event(payload)

    assert event is not None
    assert event.text == "oi hermes"
    assert event.message_id == "abc123"
    assert event.message_type == MessageType.TEXT
    assert event.source.platform == Platform.WHATSAPP
    assert event.source.chat_id == "5511999999999@s.whatsapp.net"
    assert event.source.user_id == "5511999999999@s.whatsapp.net"


@pytest.mark.asyncio
async def test_evolution_webhook_ignores_own_messages():
    adapter = _adapter()
    payload = {
        "event": "Message",
        "data": {
            "Info": {
                "ID": "abc123",
                "Chat": "5511999999999@s.whatsapp.net",
                "Sender": "5511999999999@s.whatsapp.net",
                "IsFromMe": True,
            },
            "Message": {"conversation": "sent by bot"},
        },
    }

    assert await adapter._build_evolution_message_event(payload) is None
