# -*- encoding: utf-8 -*-
"""Supporting read and utility resources for SignifyPy.

This module groups smaller request families used across many workflows:
long-running operations, OOBI retrieval and resolution, key-state reads, and
key-event reads.
"""
from signify.app.clienting import SignifyClient


class Operations:
    """Resource wrapper for polling long-running KERIA operations."""

    def __init__(self, client: SignifyClient):
        """Create an operations resource bound to one Signify client."""
        self.client = client

    def get(self, name):
        """Fetch one long-running operation by operation name."""
        res = self.client.get(f"/operations/{name}")
        return res.json()


class Oobis:
    """Resource wrapper for OOBI retrieval and resolution."""

    def __init__(self, client: SignifyClient):
        """Create an OOBI resource bound to one Signify client."""
        self.client = client

    def get(self, name, role="agent"):
        """Return role-specific OOBIs published for one identifier alias."""
        res = self.client.get(f"/identifiers/{name}/oobis?role={role}")
        return res.json()

    def resolve(self, oobi, alias=None):
        """Submit an OOBI for resolution, optionally storing it under an alias."""

        body = dict(
            url=oobi
        )

        if alias is not None:
            body["oobialias"] = alias

        res = self.client.post("/oobis", json=body)
        return res.json()


class KeyStates:
    """Resource wrapper for key-state reads and key-state queries."""

    def __init__(self, client: SignifyClient):
        """Create a key-state resource bound to one Signify client."""
        self.client = client

    def get(self, pre):
        """Fetch the current key state for one AID prefix."""
        res = self.client.get(f"/states?pre={pre}")
        return res.json()

    def list(self, pres):
        """Fetch key states for multiple prefixes in one request."""
        args = "&".join([f"pre={pre}" for pre in pres])
        res = self.client.get(f"/states?{args}")
        return res.json()

    def query(self, pre, sn=None, anchor=None):
        """Submit a key-state query with optional sequence or anchor hints."""
        body = dict(
            pre=pre
        )

        if sn is not None:
            body["sn"] = sn

        if anchor is not None:
            body["anchor"] = anchor

        res = self.client.post(f"/queries", json=body)
        return res.json()


class KeyEvents:
    """Resource wrapper for reading KERI events already known to the agent."""

    def __init__(self, client: SignifyClient):
        """Create a key-event resource bound to one Signify client."""
        self.client = client

    def get(self, pre):
        """Fetch KERI events for one AID prefix."""
        res = self.client.get(f"/events?pre={pre}")
        return res.json()

