# -*- encoding: utf-8 -*-
"""Endpoint-role authorization read helpers for SignifyPy."""
from signify.app.clienting import SignifyClient


class EndRoleAuthorizations:
    """Resource wrapper for listing endpoint-role authorization records."""

    def __init__(self, client: SignifyClient):
        """Create an end-role resource bound to one Signify client."""
        self.client = client

    def list(self, name=None, aid=None, role=None):
        """List endpoint-role authorizations by identifier alias or AID."""
        if name is not None:
            path = f"/identifiers/{name}/endroles"
        elif aid is not None:
            path = f"/endroles/{aid}"
        else:
            raise ValueError("either `aid` or `name` is required")

        if role is not None:
            path = path + f"/{role}"

        res = self.client.get(path)
        return res.json()
