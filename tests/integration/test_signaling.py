"""Live integration coverage for generic KERIA AgentSignals SSE."""

from __future__ import annotations

import json
import queue
import threading
import time

import pytest

from signify.app.clienting import SignifyClient
from tests.integration.helpers import POLL_INTERVAL, poll_until


pytestmark = pytest.mark.integration


def _same_agent_client(client: SignifyClient) -> SignifyClient:
    """Connect a second HTTP session to the same already-booted KERIA agent."""
    control = SignifyClient(
        passcode=client.bran,
        url=client.url,
        boot_url=client.boot_url,
    )
    control.connect()
    return control


def _wait_for_event(events: queue.Queue, errors: queue.Queue, *, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not errors.empty():
            raise errors.get()
        try:
            return events.get(timeout=0.1)
        except queue.Empty:
            continue

    if not errors.empty():
        raise errors.get()
    raise TimeoutError("timed out waiting for SSE signal event")


def test_agent_signals_stream_receives_signed_agent_event(client_factory):
    stream_client = client_factory()
    control_client = _same_agent_client(stream_client)
    assert control_client.agent.pre == stream_client.agent.pre

    stream = stream_client.signals().stream()
    events = queue.Queue()
    errors = queue.Queue()

    def read_first_data_event():
        try:
            for event in stream:
                if event.data:
                    events.put(event)
                    return
        except Exception as err:  # pragma: no cover - surfaced by main thread
            errors.put(err)

    reader = threading.Thread(target=read_first_data_event, daemon=True)
    reader.start()

    try:
        poll_until(
            lambda: control_client.get("/test/signals").json(),
            ready=lambda body: body["subscribers"] >= 1,
            timeout=20,
            interval=POLL_INTERVAL,
            describe="SSE subscription registration",
        )

        signal = {
            "event": "agent.signal.test",
            "event_id": "test-signal-1",
            "route": "/test/signals/request",
            "payload": {"subject": "sse-integration"},
        }
        response = control_client.post("/test/signals", json=signal)
        assert response.status_code == 202

        event = _wait_for_event(events, errors)
        assert event.event == signal["event"]
        assert event.id == signal["event_id"]

        envelope = json.loads(event.data)
        rpy = envelope["rpy"]
        assert rpy["r"] == signal["route"]
        assert rpy["a"]["subject"] == signal["payload"]["subject"]
        assert rpy["a"]["agent"] == stream_client.agent.pre
        assert stream_client.signals().verifyReplyEnvelope(
            envelope,
            route=signal["route"],
        ) is True
    finally:
        try:
            stream.close()
        except Exception:
            pass
        reader.join(timeout=5)
