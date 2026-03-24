# -*- encoding: utf-8 -*-
"""Schema read helpers for SignifyPy."""

from signify.app.clienting import SignifyClient


class Schemas:
    """Resource wrapper for schema read operations."""

    def __init__(self, client: SignifyClient):
        """Create a schemas resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA schema
                endpoints.
        """
        self.client = client

    def get(self, said):
        """Fetch one schema by SAID."""
        res = self.client.get(f"/schema/{said}")
        return res.json()

    def list(self):
        """List all schemas currently available to the remote agent."""
        res = self.client.get("/schema")
        return res.json()
