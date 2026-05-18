# -*- encoding: utf-8 -*-
"""Generic KERIA agent signaling helpers."""

from keri import kering
from keri.core import indexing, serdering


class AgentSignals:
    """Generic signed event stream for one connected KERIA agent."""

    def __init__(self, client):
        self.client = client

    def stream(self):
        """Open the authenticated generic agent SSE stream."""
        return self.client.stream(
            "/signals/stream",
            headers={"Accept": "text/event-stream"},
        )

    def verifyReplyEnvelope(self, envelope, route=None):
        """Verify one KERIA agent-signed KERI ``rpy`` envelope."""
        if self.client.agent is None:
            raise kering.ConfigurationError("client must be connected before verification")

        rserder = serdering.SerderKERI(sad=envelope["rpy"])
        if route is not None and rserder.ked.get("r") != route:
            return False

        data = rserder.ked.get("a", {})
        if data.get("agent") != self.client.agent.pre:
            return False

        sigs = envelope.get("sigs") or []
        if not sigs:
            return False

        siger = indexing.Siger(qb64=sigs[0])
        return self.client.agent.verfer.verify(sig=siger.raw, ser=rserder.raw)
