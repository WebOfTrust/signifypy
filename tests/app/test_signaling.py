# -*- encoding: utf-8 -*-
"""
SIGNIFY generic agent signaling helper tests.
"""

import pytest
from keri import kering
from keri.core import eventing, signing
from mockito import expect, mock, verifyNoUnwantedInteractions, unstub

from signify.app.signaling import AgentSignals


def signed_envelope(route="/test/signals/request", agent="agent-aid", signer=None):
    signer = signer if signer is not None else signing.Salter(raw=b"0123456789abcdef").signer()
    rpy = eventing.reply(route=route, data={"agent": agent, "payload": "value"})
    sig = signer.sign(ser=rpy.raw, index=0)
    return signer, {"rpy": rpy.ked, "sigs": [sig.qb64]}


def test_agent_signals_stream_uses_generic_endpoint():
    client = mock(strict=True)
    stream = iter([])
    expect(client, times=1).stream(
        "/signals/stream",
        headers={"Accept": "text/event-stream"},
    ).thenReturn(stream)

    assert AgentSignals(client).stream() is stream
    verifyNoUnwantedInteractions()
    unstub()


def test_agent_signals_verify_agent_signed_reply_envelope():
    signer, envelope = signed_envelope()
    client = mock({"agent": mock({"pre": "agent-aid", "verfer": signer.verfer})})

    assert AgentSignals(client).verifyReplyEnvelope(
        envelope,
        route="/test/signals/request",
    ) is True


def test_agent_signals_verify_rejects_wrong_route():
    signer, envelope = signed_envelope(route="/wrong")
    client = mock({"agent": mock({"pre": "agent-aid", "verfer": signer.verfer})})

    assert AgentSignals(client).verifyReplyEnvelope(
        envelope,
        route="/test/signals/request",
    ) is False


def test_agent_signals_verify_rejects_wrong_agent_payload():
    signer, envelope = signed_envelope(agent="wrong-agent")
    client = mock({"agent": mock({"pre": "agent-aid", "verfer": signer.verfer})})

    assert AgentSignals(client).verifyReplyEnvelope(envelope) is False


def test_agent_signals_verify_rejects_missing_signatures():
    signer, envelope = signed_envelope()
    envelope["sigs"] = []
    client = mock({"agent": mock({"pre": "agent-aid", "verfer": signer.verfer})})

    assert AgentSignals(client).verifyReplyEnvelope(envelope) is False


def test_agent_signals_verify_rejects_bad_signature():
    signer, envelope = signed_envelope()
    other = signing.Salter(raw=b"fedcba9876543210").signer()
    client = mock({"agent": mock({"pre": "agent-aid", "verfer": other.verfer})})

    assert AgentSignals(client).verifyReplyEnvelope(envelope) is False


def test_agent_signals_verify_requires_connected_agent():
    _, envelope = signed_envelope()
    client = mock({"agent": None})

    with pytest.raises(kering.ConfigurationError, match="client must be connected"):
        AgentSignals(client).verifyReplyEnvelope(envelope)
