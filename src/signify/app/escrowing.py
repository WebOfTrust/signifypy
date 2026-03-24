# -*- encoding: utf-8 -*-
"""Escrow inspection helpers for SignifyPy."""
from signify.app.clienting import SignifyClient


class Escrows:
    """Resource wrapper for inspecting escrowed replies in the agent."""

    def __init__(self, client: SignifyClient):
        """Create an escrow resource bound to one Signify client."""
        self.client = client

    def listReply(self, route=None):
        """Return escrowed reply records, optionally filtered by route."""
        params = {}
        if route is not None:
            params['route'] = route

        res = self.client.get(f"/escrows/rpy", params=params)
        return res.json()

    def getEscrowReply(self, route=None):
        """Compatibility alias for :meth:`listReply`."""
        return self.listReply(route=route)
