# -*- encoding: utf-8 -*-
"""Contact lookup helpers for SignifyPy."""
from signify.app.clienting import SignifyClient


class Contacts:
    """Resource wrapper for listing resolved contact records."""

    def __init__(self, client: SignifyClient):
        """Create a contact resource bound to one Signify client."""
        self.client = client

    def list(self, start=0, end=24):
        """List resolved contacts currently known to the remote agent.

        Parameters:
            start (int): Inclusive start offset for the requested window.
            end (int): Inclusive end offset for the requested window.

        Returns:
            dict: Window metadata and the returned contact records.
        """
        headers = dict(Range=f"contacts={start}-{end}")
        res = self.client.get(f"/contacts", headers=headers)
        # cr = res.headers["content-range"]
        # start, end, total = httping.parseRangeHeader(cr, "notes")

        contacts = res.json()
        return dict(start=0, end=len(contacts), total=len(contacts), contacts=contacts)
